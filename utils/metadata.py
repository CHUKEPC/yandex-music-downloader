def extract_metadata(track, album_name=None, total_tracks=None, total_discs=None):
    """Извлекает все доступные метаданные из объекта track"""
    metadata = {}

    try:
        # Основные данные
        if hasattr(track, 'title') and track.title:
            metadata['title'] = track.title

        if hasattr(track, 'artists') and track.artists:
            try:
                metadata['artist'] = ', '.join([a.name for a in track.artists if hasattr(a, 'name') and a.name])
            except:
                pass

        metadata['album'] = album_name

        # Данные из альбома
        if hasattr(track, 'albums') and track.albums and len(track.albums) > 0:
            try:
                album = track.albums[0]
                if not metadata.get('album') and hasattr(album, 'title') and album.title:
                    metadata['album'] = album.title

                # Исполнитель альбома
                if hasattr(album, 'artists') and album.artists:
                    try:
                        metadata['album_artist'] = ', '.join([a.name for a in album.artists if hasattr(a, 'name') and a.name])
                    except:
                        pass

                # Год альбома
                if hasattr(album, 'year') and album.year:
                    metadata['year'] = str(album.year)

                # Жанр альбома
                if hasattr(album, 'genre') and album.genre:
                    try:
                        if isinstance(album.genre, str):
                            metadata['genre'] = album.genre
                        elif hasattr(album.genre, 'name') and album.genre.name:
                            metadata['genre'] = album.genre.name
                    except:
                        pass

                # Номер трека из альбома
                if hasattr(album, 'track_position'):
                    if hasattr(album.track_position, 'index') and album.track_position.index:
                        metadata['track_number'] = str(album.track_position.index)
                    if hasattr(album.track_position, 'volume') and album.track_position.volume:
                        metadata['disc_number'] = str(album.track_position.volume)

                # Общее количество треков из альбома
                if hasattr(album, 'track_count') and album.track_count:
                    metadata['total_tracks'] = str(album.track_count)

            except Exception:
                pass

        # Год трека (если не из альбома)
        if not metadata.get('year') and hasattr(track, 'year') and track.year:
            metadata['year'] = str(track.year)

        # Жанр трека (если не из альбома)
        if not metadata.get('genre') and hasattr(track, 'genre') and track.genre:
            try:
                if isinstance(track.genre, str):
                    metadata['genre'] = track.genre
                elif hasattr(track.genre, 'name') and track.genre.name:
                    metadata['genre'] = track.genre.name
            except:
                pass

        # Номер трека напрямую из track
        if not metadata.get('track_number'):
            if hasattr(track, 'track_position') and track.track_position:
                if hasattr(track.track_position, 'index') and track.track_position.index:
                    metadata['track_number'] = str(track.track_position.index)

        # Номер диска напрямую из track
        if not metadata.get('disc_number'):
            if hasattr(track, 'track_position') and track.track_position:
                if hasattr(track.track_position, 'volume') and track.track_position.volume:
                    metadata['disc_number'] = str(track.track_position.volume)

        # Используем переданные значения (они имеют приоритет)
        if total_tracks is not None:
            metadata['total_tracks'] = str(total_tracks)

        if total_discs is not None:
            metadata['total_discs'] = str(total_discs)

        # Версия трека
        if hasattr(track, 'version') and track.version:
            metadata['version'] = track.version

        # Длительность (в секундах)
        if hasattr(track, 'duration_ms') and track.duration_ms:
            try:
                metadata['duration'] = str(int(track.duration_ms / 1000))
            except:
                pass

    except Exception as e:
        print(f"Предупреждение: ошибка при извлечении некоторых метаданных: {e}")

    return metadata