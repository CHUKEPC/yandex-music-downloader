import logging
import os
import re
import time
import requests
from tqdm import tqdm

from utils.file_utils import sanitize_filename
from downloader.track_downloader import TrackDownloader


logger = logging.getLogger(__name__)


class ContentDownloader:
    """Класс для скачивания контента (альбомы, плейлисты, артисты)"""

    def __init__(self, client, config):
        self.client = client
        self.config = config
        self.track_downloader = TrackDownloader(client, config.AUDIO_QUALITY)

    def download_single_track(self, url):
        """Скачивает один трек"""
        pattern = r"track/(\d+)"
        match = re.search(pattern, url)
        if not match:
            logger.error("Неверная ссылка на трек: %s", url)
            print("Неверная ссылка на трек")
            return

        track_id = match.group(1)
        track = self.client.tracks(track_id)[0]

        logger.info("Скачивание трека %s", url)
        self.track_downloader.download_track(track, self.config.DOWNLOAD_DIR)

    def download_album(self, url):
        """Скачивает альбом"""
        pattern = r"album/(\d+)"
        match = re.search(pattern, url)
        if not match:
            logger.error("Неверная ссылка на альбом: %s", url)
            print("Неверная ссылка на альбом")
            return

        album_id = match.group(1)
        album = self.client.albums_with_tracks(album_id)
        album_name = album.title
        logger.info("Скачивание альбома '%s' (%s)", album_name, url)

        total_tracks_all = sum(len(volume) for volume in album.volumes)
        total_discs = len(album.volumes)

        # Сингл - сохраняем в корневую папку
        if total_tracks_all == 1:
            print(f"Скачиваю сингл: {album_name}")
            for volume in album.volumes:
                for track in volume:
                    self.track_downloader.download_track(track, self.config.DOWNLOAD_DIR, album_name, total_tracks_all, total_discs)
            print(f"Сингл '{album_name}' успешно скачан в {self.config.DOWNLOAD_DIR}")
            logger.info("Сингл '%s' скачан (%s)", album_name, album_id)
        else:
            safe_album_name = sanitize_filename(album_name)
            album_dir = os.path.join(self.config.DOWNLOAD_DIR, safe_album_name)

            print(f"Скачиваю альбом: {album_name}")

            # Собираем все треки для progress bar
            all_tracks = []
            for volume_idx, volume in enumerate(album.volumes):
                tracks_in_volume = len(volume)
                for track in volume:
                    all_tracks.append((track, tracks_in_volume, total_discs))

            # Скачиваем с progress bar
            with tqdm(
                total=len(all_tracks),
                desc=f"💿 Альбом: {album_name}",
                unit=" трек",
                bar_format='{desc}: {percentage:3.0f}%|{bar}| {n}/{total} [{elapsed}<{remaining}, {rate_fmt}]',
                ncols=100,
                colour='blue',
                ascii=' ░▒▓█',
                dynamic_ncols=True
            ) as pbar:
                for track, tracks_in_volume, total_discs in all_tracks:
                    self.track_downloader.download_track(track, album_dir, album_name, tracks_in_volume, total_discs)
                    pbar.update(1)
            logger.info("Альбом '%s' скачан (%s)", album_name, album_id)

            print(f"Альбом '{album_name}' успешно скачан в {album_dir}")

    def download_playlist(self, url):
        """Скачивает плейлист"""
        pattern = r"/(?:playlist/([^/]+)|users/([^/]+)/playlists)/(\d+)|(?:/playlists/([0-9a-fA-F-]+)|playlists/lk.([0-9a-fA-F-]+))"
        match = re.search(pattern, url)
        if not match:
            logger.error("Неверная ссылка на плейлист: %s", url)
            print("Неверная ссылка на плейлист")
            return

        playlist_user = match.group(1) or match.group(2)
        playlist_id = match.group(3)
        playlist_uid = match.group(4) or match.group(5)

        # ОбработкаUID плейлистов
        if playlist_uid:
            headers = {
                'Authorization': f'OAuth {self.config.YANDEX_MUSIC_TOKEN}',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
            }

            result = False
            cnt = 0
            while not result:
                try:
                    response = requests.get(f'https://api.music.yandex.ru/playlist/{playlist_uid}', headers=headers)

                    if response.status_code == 200:
                        data = response.json()
                        if 'result' in data:
                            result_data = data['result']
                            playlist_user = result_data.get('uid')
                            playlist_id = result_data.get('kind')
                            result = True
                    else:
                        playlist_uid = f'lk.{playlist_uid}'

                except requests.exceptions.RequestException:
                    cnt += 1
                    time.sleep(2**cnt)

        try:
            playlist = self.client.users_playlists(kind=playlist_id, user_id=playlist_user)
        except:
            logger.exception("Ошибка при запросе плейлиста %s", url)
            print("Скачать данный плейлист невозможно, скорее всего в нём находятся треки, загруженные пользователем вручную")
            return

        playlist_name = playlist.title
        safe_playlist_name = sanitize_filename(playlist_name)
        playlist_dir = os.path.join(self.config.DOWNLOAD_DIR, safe_playlist_name)

        print(f"Скачиваю плейлист: {playlist_name}")
        logger.info("Скачивание плейлиста '%s' (%s)", playlist_name, url)

        # Собираем все треки для progress bar
        tracks_to_download = []
        for track_item in playlist.tracks:
            try:
                if hasattr(track_item, 'track') and track_item.track:
                    track = track_item.track
                else:
                    track_id = f"{track_item.id}:{track_item.album_id}"
                    track = self.client.tracks(track_id)[0]
                if track:
                    tracks_to_download.append(track)
            except Exception as e:
                logger.warning("Ошибка при получении трека из плейлиста: %s", e)
                print(f"Ошибка при получении трека из плейлиста: {e}")
                continue

        # Скачиваем с progress bar
        with tqdm(
            total=len(tracks_to_download),
            desc=f"🎶 Плейлист: {playlist_name}",
            unit=" трек",
            bar_format='{desc}: {percentage:3.0f}%|{bar}| {n}/{total} [{elapsed}<{remaining}, {rate_fmt}]',
            ncols=100,
            colour='magenta',
            ascii=' ░▒▓█',
            dynamic_ncols=True
        ) as pbar:
            for track_item in playlist.tracks:
                try:
                    if hasattr(track_item, 'track') and track_item.track:
                        track = track_item.track
                    else:
                        track_id = f"{track_item.id}:{track_item.album_id}"
                        track = self.client.tracks(track_id)[0]

                    if track:
                        self.track_downloader.download_track(track, playlist_dir)
                        pbar.update(1)
                except Exception as e:
                    logger.warning("Ошибка при скачивании трека из плейлиста: %s", e)
                    print(f"Ошибка при скачивании трека из плейлиста: {e}")
                    pbar.update(1)  # Обновляем прогресс даже при ошибке
                    continue

        print(f"Плейлист '{playlist_name}' успешно скачан в {playlist_dir}")
        logger.info("Плейлист '%s' скачан (%s)", playlist_name, url)

    def download_artist(self, url):
        """Скачивает все треки и альбомы артиста"""
        pattern = r"artist/(\d+)"
        match = re.search(pattern, url)
        if not match:
            logger.error("Неверная ссылка на артиста: %s", url)
            print("Неверная ссылка на артиста")
            return

        artist_id = match.group(1)

        try:
            artist = self.client.artists(artist_id)[0]
            artist_name = artist.name

            print(f"Скачиваю треки артиста: {artist_name}")
            logger.info("Скачивание артиста '%s' (%s)", artist_name, url)

            safe_artist_name = sanitize_filename(artist_name)
            artist_dir = os.path.join(self.config.DOWNLOAD_DIR, "artists", safe_artist_name)

            # Скачиваем альбомы
            albums = self.client.artists_direct_albums(artist_id, page_size=100)

            if albums and hasattr(albums, 'albums'):
                print(f"Найдено альбомов: {len(albums.albums)}")
                logger.info("Найдено альбомов артиста %s: %s", artist_name, len(albums.albums))

                for album in albums.albums:
                    try:
                        full_album = self.client.albums_with_tracks(album.id)
                        album_name = full_album.title

                        total_tracks = sum(len(volume) for volume in full_album.volumes)
                        total_discs = len(full_album.volumes)

                        if total_tracks == 1:
                            print(f"\nСкачиваю сингл: {album_name}")
                            singles_dir = os.path.join(artist_dir, "Singles & Other Tracks")

                            for volume in full_album.volumes:
                                for track in volume:
                                    self.track_downloader.download_track(track, singles_dir, album_name, total_tracks, total_discs)

                            print(f"Сингл '{album_name}' скачан")
                        else:
                            safe_album_name = sanitize_filename(album_name)
                            album_dir_path = os.path.join(artist_dir, safe_album_name)

                            print(f"\nСкачиваю альбом: {album_name}")

                            # Собираем все треки для progress bar
                            all_tracks = []
                            for volume_idx, volume in enumerate(full_album.volumes):
                                tracks_in_volume = len(volume)
                                for track in volume:
                                    all_tracks.append((track, tracks_in_volume, total_discs))

                            # Скачиваем с progress bar
                            with tqdm(
                                total=len(all_tracks),
                                desc=f"💿 Альбом: {album_name}",
                                unit=" трек",
                                bar_format='{desc}: {percentage:3.0f}%|{bar}| {n}/{total} [{elapsed}<{remaining}, {rate_fmt}]',
                                ncols=100,
                                colour='blue',
                                ascii=' ░▒▓█',
                                dynamic_ncols=True
                            ) as pbar:
                                for track, tracks_in_volume, total_discs in all_tracks:
                                    self.track_downloader.download_track(track, album_dir_path, album_name, tracks_in_volume, total_discs)
                                    pbar.update(1)

                            print(f"Альбом '{album_name}' скачан")
                            logger.info("Альбом '%s' артиста '%s' скачан", album_name, artist_name)

                    except Exception as e:
                        logger.warning("Ошибка при скачивании альбома %s: %s", album.title, e)
                        print(f"Ошибка при скачивании альбома {album.title}: {e}")
                        continue

            # Скачиваем отдельные треки
            tracks = self.client.artists_tracks(artist_id, page_size=100)

            if tracks and hasattr(tracks, 'tracks'):
                print(f"\nНайдено отдельных треков: {len(tracks.tracks)}")
                logger.info("Найдено отдельных треков артиста %s: %s", artist_name, len(tracks.tracks))

                singles_dir = os.path.join(artist_dir, "Singles & Other Tracks")

                # Скачиваем с progress bar
                with tqdm(
                    total=len(tracks.tracks),
                    desc="🎵 Отдельные треки",
                    unit=" трек",
                    bar_format='{desc}: {percentage:3.0f}%|{bar}| {n}/{total} [{elapsed}<{remaining}, {rate_fmt}]',
                    ncols=100,
                    colour='yellow',
                    ascii=' ░▒▓█',
                    dynamic_ncols=True
                ) as pbar:
                    for track in tracks.tracks:
                        try:
                            self.track_downloader.download_track(track, singles_dir)
                            pbar.update(1)
                        except Exception as e:
                            logger.warning("Ошибка при скачивании трека %s: %s", track.title, e)
                            print(f"Ошибка при скачивании трека {track.title}: {e}")
                            pbar.update(1)  # Обновляем прогресс даже при ошибке
                            continue

            print(f"\nВсе треки артиста '{artist_name}' успешно скачаны в {artist_dir}")
            logger.info("Артист '%s' скачан в %s", artist_name, artist_dir)

        except Exception as e:
            logger.exception("Ошибка при получении информации об артисте: %s", e)
            print(f"Ошибка при получении информации об артисте: {e}")