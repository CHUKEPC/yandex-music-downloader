> 🇷🇺 [Русская версия](README_RU.md)

# Yandex Music Downloader

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A convenient tool for downloading music from Yandex.Music with full metadata and cover art.

---

## Features

- Download tracks, albums, playlists, and full artist discographies
- Beautiful progress bar with download status
- Automatic cover art embedding
- Full metadata support (artist, album, year, genre, track number, etc.)
- Smart file organization (separate folders for albums, singles in one folder)
- Multiple audio format support

## Prerequisites

- Python 3.7+
- Yandex.Music token

## Installation

1. Clone the repository:
```bash
git clone https://github.com/CHUKEPC/yandex-music-downloader.git
cd yandex-music-downloader
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a configuration file:
```bash
cp config.example.py config.py
```

4. Edit `config.py` and add your token (instructions for obtaining a token: https://github.com/MarshalX/yandex-music-api/discussions/513)

### Audio Quality Settings

You can choose the download quality in `config.py`:

- **`lossless`** — Lossless quality (FLAC, ~1000 kbps)
  - Maximum audio quality
  - Large file sizes (~30-50 MB per track)
  - Requires Yandex.Plus subscription

- **`hq`** — High quality (MP3 320 kbps) — **Recommended**
  - Excellent audio quality
  - Reasonable file sizes (~7-12 MB per track)

- **`nq`** — Normal quality (MP3 192 kbps)
  - Good quality for everyday listening
  - Small file sizes (~4-7 MB per track)

### Logging

Logs are written to a file only (no console output) and configured in `config.py`:

- `LOGGING_ENABLED` — enable/disable logging (True/False)
- `LOG_FILE` — path to the log file (default: `logs/app.log`, directory is created automatically)
- `LOG_LEVEL` — level (`DEBUG`/`INFO`/`WARNING`/`ERROR`/`CRITICAL`)

By default, noise from external libraries (e.g., `yandex_music`) is reduced to WARNING.

### Parallel Downloads

To speed up album and playlist downloads, you can enable multithreading:

- `MAX_CONCURRENT_DOWNLOADS` — number of simultaneous downloads (1 = single-threaded, default is 4)

### Metadata Caching

To speed up repeated downloads, track metadata can be cached to disk:

- `METADATA_CACHE_ENABLED` — enable/disable cache (True/False)
- `METADATA_CACHE_FILE` — path to the cache file (default: `cache/metadata.json`, directory is created automatically)
- `METADATA_CACHE_TTL_HOURS` — entry lifetime in hours (0 = no expiration)

The cache works transparently: on repeated downloads, metadata is loaded from the file if the entry hasn't expired.

## Usage

Run the script:
```bash
python main.py
```

Enter a link to:
- **Track**: `https://music.yandex.ru/album/123456/track/789012`
- **Album**: `https://music.yandex.ru/album/123456`
- **Playlist**: `https://music.yandex.ru/users/username/playlists/123`
- **Artist**: `https://music.yandex.ru/artist/123456`

During download, you'll see a progress bar showing:
- Completion percentage
- Number of downloaded tracks (for albums/playlists)
- Download speed
- Estimated time remaining

## Running with Docker

1. Build the image:
```bash
docker build -t yandex-music-downloader .
```

2. Run the container:
```bash
docker run --rm -it \
  -e YANDEX_MUSIC_TOKEN="your_token" \
  -e AUDIO_QUALITY="hq" \
  -v "$(pwd)/music:/app/music" \
  -v "$(pwd)/logs:/app/logs" \
  -v "$(pwd)/cache:/app/cache" \
  yandex-music-downloader
```

Available environment variables (all have defaults from `config.py`):
- `YANDEX_MUSIC_TOKEN` — Yandex.Music token (required)
- `AUDIO_QUALITY` — `lossless` / `hq` / `nq`
- `DOWNLOAD_DIR` — download folder (default: `/app/music`)
- `LOGGING_ENABLED`, `LOG_FILE`, `LOG_LEVEL`
- `METADATA_CACHE_ENABLED`, `METADATA_CACHE_FILE`, `METADATA_CACHE_TTL_HOURS`
- `MAX_CONCURRENT_DOWNLOADS`

## Project Structure

```
yandex-music-downloader/
├── main.py                      # Entry point
├── config.py                    # Configuration
├── requirements.txt             # Dependencies
├── utils/
│   ├── __init__.py
│   ├── file_utils.py           # File handling utilities
│   └── metadata.py             # Metadata processing
├── audio/
│   ├── __init__.py
│   └── audio_processor.py      # Audio file processing
└── downloader/
    ├── __init__.py
    ├── track_downloader.py     # Track downloading
    └── content_downloader.py   # Album/playlist/artist downloading
```

## Downloaded Files Organization

```
music/
├── Artist Name - Track Title.mp3          # Individual tracks
├── Album Name/                            # Albums
│   ├── Artist - Track 1.mp3
│   └── Artist - Track 2.mp3
├── Playlist Name/                         # Playlists
│   └── ...
└── artists/
    └── Artist Name/
        ├── Album Name/                    # Artist albums
        │   └── ...
        └── Singles & Other Tracks/        # Singles
            └── ...
```

## Dependencies

- `yandex-music` — Unofficial library for Yandex.Music API
- `mutagen` — Audio file metadata handling
- `requests` — HTTP requests
- `pycryptodome` — Decryption of encrypted audio files (FLAC in MP4 container) for lossless downloads
- `tqdm` — Progress bar for tracking download progress

## Limitations

- Uses unofficial Yandex.Music API
- An active subscription may be required for some content
- Some playlists with user-uploaded content may not be downloadable

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Legal Notice

This tool is intended for personal use only. Make sure you have the rights to download the music. Respect copyright laws.

## Contributing

Contributions are welcome! If you have ideas for improvement:

1. Fork the project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Author

**CHUKEPC**
- GitHub: [@CHUKEPC](https://github.com/CHUKEPC)
- Telegram: [@ArtyomRoyal](https://t.me/ArtyomRoyal)
