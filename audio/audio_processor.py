import os
import base64
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, APIC, TALB, TPE2, TDRC, TCON, TRCK, TPOS, TIT3, COMM, TENC
from mutagen.flac import FLAC, Picture
from mutagen.mp4 import MP4, MP4Cover
from mutagen.oggvorbis import OggVorbis
from mutagen.oggopus import OggOpus

from utils.metadata import extract_metadata


class UnsupportedAudioFormatError(Exception):
    pass


class AudioProcessor:
    """Класс для обработки аудио файлов"""

    @staticmethod
    def process_mp3(audio, metadata):
        """Применяет теги для MP3"""
        if metadata.get('title'):
            audio['TIT2'] = TIT2(encoding=3, text=metadata['title'])
        if metadata.get('artist'):
            audio['TPE1'] = TPE1(encoding=3, text=metadata['artist'])
        if metadata.get('album'):
            audio['TALB'] = TALB(encoding=3, text=metadata['album'])
        if metadata.get('album_artist'):
            audio['TPE2'] = TPE2(encoding=3, text=metadata['album_artist'])
        if metadata.get('year'):
            audio['TDRC'] = TDRC(encoding=3, text=metadata['year'])
        if metadata.get('genre'):
            audio['TCON'] = TCON(encoding=3, text=metadata['genre'])
        if metadata.get('track_number'):
            track_text = metadata['track_number']
            if metadata.get('total_tracks'):
                track_text += '/' + metadata['total_tracks']
            audio['TRCK'] = TRCK(encoding=3, text=track_text)
        if metadata.get('disc_number'):
            disc_text = metadata['disc_number']
            if metadata.get('total_discs'):
                disc_text += '/' + metadata['total_discs']
            audio['TPOS'] = TPOS(encoding=3, text=disc_text)
        if metadata.get('version'):
            audio['TIT3'] = TIT3(encoding=3, text=metadata['version'])
        audio['COMM'] = COMM(encoding=3, lang='eng', desc='', text='Downloaded from Yandex Music')
        audio['TENC'] = TENC(encoding=3, text='Yandex Music Downloader')

    @staticmethod
    def process_flac_ogg(audio, metadata):
        """Применяет теги для FLAC/OGG/OPUS"""
        if metadata.get('title'):
            audio['title'] = metadata['title']
        if metadata.get('artist'):
            audio['artist'] = metadata['artist']
        if metadata.get('album'):
            audio['album'] = metadata['album']
        if metadata.get('album_artist'):
            audio['albumartist'] = metadata['album_artist']
        if metadata.get('year'):
            audio['date'] = metadata['year']
        if metadata.get('genre'):
            audio['genre'] = metadata['genre']
        if metadata.get('track_number'):
            audio['tracknumber'] = metadata['track_number']
        if metadata.get('total_tracks'):
            audio['tracktotal'] = metadata['total_tracks']
        if metadata.get('disc_number'):
            audio['discnumber'] = metadata['disc_number']
        if metadata.get('total_discs'):
            audio['disctotal'] = metadata['total_discs']
        if metadata.get('version'):
            audio['version'] = metadata['version']
        audio['comment'] = 'Downloaded from Yandex Music'

    @staticmethod
    def process_mp4(audio, metadata):
        """Применяет теги для MP4/M4A"""
        if metadata.get('title'):
            audio['\xa9nam'] = metadata['title']
        if metadata.get('artist'):
            audio['\xa9ART'] = metadata['artist']
        if metadata.get('album'):
            audio['\xa9alb'] = metadata['album']
        if metadata.get('album_artist'):
            audio['aART'] = metadata['album_artist']
        if metadata.get('year'):
            audio['\xa9day'] = metadata['year']
        if metadata.get('genre'):
            audio['\xa9gen'] = metadata['genre']
        if metadata.get('track_number'):
            track_num = int(metadata['track_number'])
            total_tracks_num = int(metadata['total_tracks']) if metadata.get('total_tracks') else 0
            audio['trkn'] = [(track_num, total_tracks_num)]
        if metadata.get('disc_number'):
            disc_num = int(metadata['disc_number'])
            total_discs_num = int(metadata['total_discs']) if metadata.get('total_discs') else 0
            audio['disk'] = [(disc_num, total_discs_num)]

        comment_parts = []
        if metadata.get('version'):
            comment_parts.append(f"Version: {metadata['version']}")
        comment_parts.append('Downloaded from Yandex Music')
        audio['\xa9cmt'] = ' | '.join(comment_parts)

    @staticmethod
    def add_cover_mp3(audio, cover_data):
        """Добавляет обложку для MP3"""
        audio['APIC'] = APIC(
            encoding=3,
            mime='image/jpeg',
            type=3,
            desc='Cover',
            data=cover_data
        )

    @staticmethod
    def add_cover_flac(audio, cover_data):
        """Добавляет обложку для FLAC"""
        image = Picture()
        image.type = 3
        image.mime = 'image/jpeg'
        image.desc = 'Cover'
        image.data = cover_data
        audio.add_picture(image)

    @staticmethod
    def add_cover_ogg(audio, cover_data):
        """Добавляет обложку для OGG/OPUS"""
        audio['metadata_block_picture'] = [base64.b64encode(cover_data).decode('ascii')]

    @staticmethod
    def add_cover_mp4(audio, cover_data):
        """Добавляет обложку для MP4/M4A"""
        audio['covr'] = [MP4Cover(cover_data, imageformat=MP4Cover.FORMAT_JPEG)]

    @classmethod
    def process_audio(cls, temp_file_path, track, downloaded_cover, album_name=None, total_tracks=None, total_discs=None):
        """Применяет все доступные теги и обложку к аудио файлу"""
        file_extension = os.path.splitext(temp_file_path)[1].lower()

        # Открываем файл
        if file_extension == '.mp3':
            audio = MP3(temp_file_path, ID3=ID3)
        elif file_extension == '.flac':
            audio = FLAC(temp_file_path)
        elif file_extension in ['.m4a', '.mp4']:
            audio = MP4(temp_file_path)
        elif file_extension in ['.ogg', '.oga']:
            audio = OggVorbis(temp_file_path)
        elif file_extension == '.opus':
            audio = OggOpus(temp_file_path)
        else:
            raise UnsupportedAudioFormatError(f"Неподдерживаемый формат аудио: {file_extension}")

        # Очистка старых тегов
        if hasattr(audio, 'clear'):
            audio.clear()
        elif hasattr(audio, 'delete'):
            audio.delete()

        # Извлекаем метаданные
        metadata = extract_metadata(track, album_name, total_tracks, total_discs)

        # Применяем теги в зависимости от формата
        if isinstance(audio, MP3):
            cls.process_mp3(audio, metadata)
        elif isinstance(audio, (FLAC, OggVorbis, OggOpus)):
            cls.process_flac_ogg(audio, metadata)
        elif isinstance(audio, MP4):
            cls.process_mp4(audio, metadata)

        # Применяем обложку
        if downloaded_cover:
            if isinstance(audio, MP3):
                cls.add_cover_mp3(audio, downloaded_cover)
            elif isinstance(audio, FLAC):
                cls.add_cover_flac(audio, downloaded_cover)
            elif isinstance(audio, (OggVorbis, OggOpus)):
                cls.add_cover_ogg(audio, downloaded_cover)
            elif isinstance(audio, MP4):
                cls.add_cover_mp4(audio, downloaded_cover)

        audio.save()