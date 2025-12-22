from yandex_music import Client
import config
from downloader.content_downloader import ContentDownloader


def main():
    """Главная функция"""
    print("YandexMusicDownloader")
    print("=" * 50)

    # Инициализация клиента
    client = Client(config.YANDEX_MUSIC_TOKEN).init()

    # Показываем текущие настройки
    quality_names = {
        "lossless": "Lossless (FLAC, ~1000 kbps)",
        "hq": "High Quality (MP3 320 kbps)",
        "nq": "Normal Quality (MP3 192 kbps)"
    }
    print(f"Качество аудио: {quality_names.get(config.AUDIO_QUALITY, config.AUDIO_QUALITY)}")
    print(f"Директория: {config.DOWNLOAD_DIR}")
    print("=" * 50)

    # Создаём загрузчик
    downloader = ContentDownloader(client, config)

    url = input("Введите ссылку на трек, альбом, плейлист или артиста: ").strip()

    if not url.startswith('https://music.yandex.ru/'):
        print("Неверная ссылка. Должна начинаться с https://music.yandex.ru/")
        return

    # Определяем тип контента и скачиваем
    if 'track' in url:
        downloader.download_single_track(url)
    elif 'album' in url:
        downloader.download_album(url)
    elif 'playlist' in url:
        downloader.download_playlist(url)
    elif 'artist' in url:
        downloader.download_artist(url)
    else:
        print("Неверная ссылка. Поддерживаются треки, альбомы, плейлисты и артисты.")


if __name__ == '__main__':
    main()