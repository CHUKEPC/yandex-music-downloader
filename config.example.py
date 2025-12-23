"""
Конфигурация приложения
Скопируйте этот файл в config.py и заполните своими данными
"""

# Токен для доступа к Yandex Music API
# Получите токен Яндекс Музыки здесь: https://github.com/MarshalX/yandex-music-api/discussions/513
YANDEX_MUSIC_TOKEN = "your_token_here"

# Директория для сохранения музыки
DOWNLOAD_DIR = "music"

# Качество аудио при скачивании
# Доступные значения:
#   "lossless" - без потерь (FLAC, ~1000 kbps) - максимальное качество
#   "hq"       - высокое качество (MP3 320 kbps) - рекомендуется
#   "nq"       - нормальное качество (MP3 192 kbps) - экономия места
AUDIO_QUALITY = "hq"

# Логирование
# Если LOGGING_ENABLED = True — логи пишутся в файл LOG_FILE
# Если False — логирование полностью отключено
LOGGING_ENABLED = True
LOG_FILE = "logs/app.log"
LOG_LEVEL = "INFO"

# Кэширование метаданных
METADATA_CACHE_ENABLED = True
METADATA_CACHE_FILE = "cache/metadata.json"
METADATA_CACHE_TTL_HOURS = 24