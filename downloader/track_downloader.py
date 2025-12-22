import os
import tempfile
import shutil
import requests
import hmac
import hashlib
import base64
import typing
import random
import time
from Crypto.Cipher import AES

from utils.file_utils import sanitize_filename, detect_audio_format
from audio.audio_processor import AudioProcessor, UnsupportedAudioFormatError
from yandex_music.utils.sign_request import DEFAULT_SIGN_KEY


class TrackDownloader:
    """Класс для скачивания треков"""

    # Секретный ключ для получения FLAC
    SECRET = DEFAULT_SIGN_KEY

    def __init__(self, client, audio_quality="hq"):
        self.client = client
        self.audio_quality = audio_quality

    def _decrypt_data(self, data: bytes, key: str) -> bytes:
        """Расшифровывает данные используя AES-CTR
        nonce равен 12 нулям согласно документации"""
        nonce = bytes.fromhex('00' * 12)  # 12 нулей в hex формате
        aes = AES.new(
            key=bytes.fromhex(key),
            nonce=nonce,
            mode=AES.MODE_CTR,
        )
        return aes.decrypt(data)

    def _download_lossless(self, track_id, temp_file_path):
        """Скачивает трек в FLAC (lossless) используя прямой API
        Возвращает кортеж (success: bool, codec: str) где codec может быть 'flac' или 'flac-mp4'
        Использует тот же подход что и рабочий код из yandex-music-downloader-main"""
        try:
            # Используем точно такой же подход как в рабочем коде
            # Список всех доступных кодеков (как в FILE_FORMAT_MAPPING)
            codecs_list = ['flac', 'flac-mp4', 'mp3', 'aac', 'he-aac', 'aac-mp4', 'he-aac-mp4']

            # Создаем параметры запроса точно как в рабочем коде
            timestamp = int(time.time())
            params = {
                'ts': timestamp,
                'trackId': track_id,
                'quality': 'lossless',
                'codecs': ','.join(codecs_list),  # Все кодеки сразу, как в рабочем коде
                'transports': 'encraw',  # Используем encraw как в рабочем коде
            }

            # Формируем HMAC подпись из значений параметров (точно как в рабочем коде)
            sign_data = ''.join(str(e) for e in params.values()).replace(',', '')
            hmac_sign = hmac.new(
                self.SECRET.encode('utf-8'),
                sign_data.encode('utf-8'),
                hashlib.sha256
            )
            sign = base64.b64encode(hmac_sign.digest()).decode('utf-8')[:-1]
            params['sign'] = sign

            # Используем встроенный метод клиента для запроса
            resp = self.client.request.get(
                'https://api.music.yandex.net/get-file-info',
                params=params
            )
            resp = typing.cast(dict, resp)

            # Проверяем наличие ошибок
            if 'error' in resp:
                error_name = resp['error'].get('name', 'unknown')
                if error_name == 'no-rights':
                    print("FLAC недоступен для этого трека (нет прав), используется стандартное качество")
                else:
                    print(f"Ошибка API: {error_name}")
                return False, None

            # Получаем информацию о скачивании (как в рабочем коде)
            download_info = resp.get('download_info')
            if not download_info:
                return False, None

            # Получаем кодек
            codec = download_info.get('codec', '')

            # Проверяем что это FLAC (чистый или в MP4)
            if codec not in ['flac', 'flac-mp4']:
                print(f"FLAC недоступен, доступен только: {codec}")
                return False, None

            # Получаем URLs (может быть несколько)
            urls = download_info.get('urls', [])
            if not urls:
                return False, None

            # Выбираем случайный URL
            download_url = random.choice(urls)

            # Скачиваем файл используя метод клиента
            track_data = self.client.request.retrieve(download_url)

            # Проверяем нужна ли расшифровка
            # Если transport = "encraw" и есть поле "key", нужно расшифровать
            decryption_key = download_info.get('key')
            if decryption_key:
                track_data = self._decrypt_data(track_data, decryption_key)

            # Сохраняем файл (как есть - flac или flac-mp4)
            with open(temp_file_path, 'wb') as f:
                f.write(track_data)

            return True, codec

        except Exception as e:
            print(f"Ошибка при скачивании FLAC: {e}")
            return False, None

    def _get_best_codec(self, track):
        """Определяет лучший доступный кодек в зависимости от настроек качества"""
        try:
            # Получаем информацию о доступных кодеках
            download_info = track.get_download_info()

            if not download_info:
                print("Предупреждение: Информация о скачивании недоступна")
                return None

            # Сортируем по битрейту (по убыванию)
            download_info = sorted(download_info, key=lambda x: x.bitrate_in_kbps, reverse=True)

            # Для lossless используем специальный метод
            if self.audio_quality == "lossless":
                # Проверяем есть ли вообще FLAC в списке
                has_flac = any(info.codec == "flac" for info in download_info)
                if has_flac:
                    # Вернем None, будем использовать прямой API
                    return None
                else:
                    print("FLAC недоступен в стандартном API, используется максимальное качество")
                    return download_info[0]

            elif self.audio_quality == "hq":
                # Ищем MP3 320 kbps или ближайший по качеству
                for info in download_info:
                    if info.codec == "mp3" and info.bitrate_in_kbps >= 320:
                        print(f"Качество: MP3 {info.bitrate_in_kbps} kbps")
                        return info
                # Если точно 320 нет, берем максимальный MP3
                mp3_codecs = [info for info in download_info if info.codec == "mp3"]
                if mp3_codecs:
                    print(f"Качество: MP3 {mp3_codecs[0].bitrate_in_kbps} kbps")
                    return mp3_codecs[0]
                # Если MP3 недоступен, берем максимальный битрейт
                print(f"MP3 недоступен, используем: {download_info[0].codec.upper()} {download_info[0].bitrate_in_kbps} kbps")
                return download_info[0]

            elif self.audio_quality == "nq":
                # Ищем MP3 192 kbps или ближайший
                for info in download_info:
                    if info.codec == "mp3" and 128 <= info.bitrate_in_kbps <= 192:
                        print(f"Качество: MP3 {info.bitrate_in_kbps} kbps")
                        return info
                # Если нет подходящего, берем минимальный MP3
                mp3_codecs = [info for info in download_info if info.codec == "mp3"]
                if mp3_codecs:
                    print(f"Качество: MP3 {mp3_codecs[-1].bitrate_in_kbps} kbps")
                    return mp3_codecs[-1]
                # Если MP3 недоступен, берем минимальный битрейт
                print(f"MP3 недоступен, используем: {download_info[-1].codec.upper()} {download_info[-1].bitrate_in_kbps} kbps")
                return download_info[-1]

            # По умолчанию максимальное качество
            return download_info[0]

        except Exception as e:
            print(f"Ошибка при выборе кодека: {e}")
            return None

    def download_track(self, track, output_dir, album_name=None, total_tracks=None, total_discs=None):
        """Скачивает трек и сохраняет его локально"""
        artist = ', '.join(artist.name for artist in track.artists)
        title = track.title

        print(f"Скачиваю: {artist} - {title}")
        # Специальная обработка для lossless
        if self.audio_quality == "lossless":
            # Пробуем скачать через прямой API
            # Сначала создаем временный файл без расширения, потом определим правильное
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file_path = temp_file.name

            success, codec = self._download_lossless(track.id, temp_file_path)

            if not success:
                # Если не удалось через прямой API, используем стандартный метод
                os.unlink(temp_file_path)
                codec_info = self._get_best_codec(track)

                if not codec_info:
                    print(f"Ошибка: Не удалось получить информацию о скачивании для трека '{title}'")
                    return

                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    codec_info.download(temp_file.name)
                    temp_file_path = temp_file.name

                file_ext = detect_audio_format(temp_file_path)
                temp_file_with_ext = temp_file_path + file_ext
                shutil.move(temp_file_path, temp_file_with_ext)
                temp_file_path = temp_file_with_ext
            else:
                # Определяем правильное расширение на основе кодека
                if codec == 'flac-mp4':
                    # FLAC в контейнере MP4 - используем расширение .m4a
                    file_ext = '.m4a'
                    temp_file_with_ext = temp_file_path + file_ext
                    shutil.move(temp_file_path, temp_file_with_ext)
                    temp_file_path = temp_file_with_ext
                else:
                    # Чистый FLAC
                    file_ext = '.flac'
                    temp_file_with_ext = temp_file_path + file_ext
                    shutil.move(temp_file_path, temp_file_with_ext)
                    temp_file_path = temp_file_with_ext
        else:
            # Стандартная обработка для hq и nq
            codec_info = self._get_best_codec(track)

            if not codec_info:
                print(f"Ошибка: Не удалось получить информацию о скачивании для трека '{title}'")
                return

            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                codec_info.download(temp_file.name)
                temp_file_path = temp_file.name

            file_ext = detect_audio_format(temp_file_path)
            temp_file_with_ext = temp_file_path + file_ext
            shutil.move(temp_file_path, temp_file_with_ext)
            temp_file_path = temp_file_with_ext

        # Получаем обложку
        cover_content = None
        if track.cover_uri:
            cover_url = f"https://{track.cover_uri.replace('%%', '200x200')}"
            try:
                cover_content = requests.get(cover_url).content
            except:
                pass

        # Применяем метаданные
        try:
            AudioProcessor.process_audio(temp_file_path, track, cover_content, album_name, total_tracks, total_discs)
        except UnsupportedAudioFormatError as e:
            print(f"Ошибка: {e}")
            os.unlink(temp_file_path)
            return

        # Сохраняем файл
        safe_artist = sanitize_filename(artist)
        safe_title = sanitize_filename(title)
        filename = f"{safe_artist} - {safe_title}{file_ext}"

        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, filename)
        shutil.move(temp_file_path, output_path)
        print(f"Сохранено: {output_path}")