import os
import re
import time
import requests

from utils.file_utils import sanitize_filename
from downloader.track_downloader import TrackDownloader


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
            print("Неверная ссылка на трек")
            return

        track_id = match.group(1)
        track = self.client.tracks(track_id)[0]

        self.track_downloader.download_track(track, self.config.DOWNLOAD_DIR)

    def download_album(self, url):
        """Скачивает альбом"""
        pattern = r"album/(\d+)"
        match = re.search(pattern, url)
        if not match:
            print("Неверная ссылка на альбом")
            return

        album_id = match.group(1)
        album = self.client.albums_with_tracks(album_id)
        album_name = album.title

        total_tracks_all = sum(len(volume) for volume in album.volumes)
        total_discs = len(album.volumes)

        # Сингл - сохраняем в корневую папку
        if total_tracks_all == 1:
            print(f"Скачиваю сингл: {album_name}")
            for volume in album.volumes:
                for track in volume:
                    self.track_downloader.download_track(track, self.config.DOWNLOAD_DIR, album_name, total_tracks_all, total_discs)
            print(f"Сингл '{album_name}' успешно скачан в {self.config.DOWNLOAD_DIR}")
        else:
            safe_album_name = sanitize_filename(album_name)
            album_dir = os.path.join(self.config.DOWNLOAD_DIR, safe_album_name)

            print(f"Скачиваю альбом: {album_name}")

            for volume_idx, volume in enumerate(album.volumes):
                tracks_in_volume = len(volume)
                for track in volume:
                    self.track_downloader.download_track(track, album_dir, album_name, tracks_in_volume, total_discs)

            print(f"Альбом '{album_name}' успешно скачан в {album_dir}")

    def download_playlist(self, url):
        """Скачивает плейлист"""
        pattern = r"/(?:playlist/([^/]+)|users/([^/]+)/playlists)/(\d+)|(?:/playlists/([0-9a-fA-F-]+)|playlists/lk.([0-9a-fA-F-]+))"
        match = re.search(pattern, url)
        if not match:
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
            print("Скачать данный плейлист невозможно, скорее всего в нём находятся треки, загруженные пользователем вручную")
            return

        playlist_name = playlist.title
        safe_playlist_name = sanitize_filename(playlist_name)
        playlist_dir = os.path.join(self.config.DOWNLOAD_DIR, safe_playlist_name)

        print(f"Скачиваю плейлист: {playlist_name}")

        for track_item in playlist.tracks:
            try:
                if hasattr(track_item, 'track') and track_item.track:
                    track = track_item.track
                else:
                    track_id = f"{track_item.id}:{track_item.album_id}"
                    track = self.client.tracks(track_id)[0]

                if track:
                    self.track_downloader.download_track(track, playlist_dir)
            except Exception as e:
                print(f"Ошибка при скачивании трека из плейлиста: {e}")
                continue

        print(f"Плейлист '{playlist_name}' успешно скачан в {playlist_dir}")

    def download_artist(self, url):
        """Скачивает все треки и альбомы артиста"""
        pattern = r"artist/(\d+)"
        match = re.search(pattern, url)
        if not match:
            print("Неверная ссылка на артиста")
            return

        artist_id = match.group(1)

        try:
            artist = self.client.artists(artist_id)[0]
            artist_name = artist.name

            print(f"Скачиваю треки артиста: {artist_name}")

            safe_artist_name = sanitize_filename(artist_name)
            artist_dir = os.path.join(self.config.DOWNLOAD_DIR, "artists", safe_artist_name)

            # Скачиваем альбомы
            albums = self.client.artists_direct_albums(artist_id, page_size=100)

            if albums and hasattr(albums, 'albums'):
                print(f"Найдено альбомов: {len(albums.albums)}")

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

                            for volume_idx, volume in enumerate(full_album.volumes):
                                tracks_in_volume = len(volume)
                                for track in volume:
                                    self.track_downloader.download_track(track, album_dir_path, album_name, tracks_in_volume, total_discs)

                            print(f"Альбом '{album_name}' скачан")

                    except Exception as e:
                        print(f"Ошибка при скачивании альбома {album.title}: {e}")
                        continue

            # Скачиваем отдельные треки
            tracks = self.client.artists_tracks(artist_id, page_size=100)

            if tracks and hasattr(tracks, 'tracks'):
                print(f"\nНайдено отдельных треков: {len(tracks.tracks)}")

                singles_dir = os.path.join(artist_dir, "Singles & Other Tracks")

                for track in tracks.tracks:
                    try:
                        self.track_downloader.download_track(track, singles_dir)
                    except Exception as e:
                        print(f"Ошибка при скачивании трека {track.title}: {e}")
                        continue

            print(f"\nВсе треки артиста '{artist_name}' успешно скачаны в {artist_dir}")

        except Exception as e:
            print(f"Ошибка при получении информации об артисте: {e}")