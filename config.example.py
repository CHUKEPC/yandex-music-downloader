"""
Конфигурация приложения (пример)
Скопируйте этот файл в config.py или используйте переменные окружения (.env)
"""
import os


def _get_bool(env_var: str, default: bool) -> bool:
    """Получить булево значение из переменной окружения."""
    value = os.getenv(env_var)
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _get_int(env_var: str, default: int) -> int:
    """Получить целое значение из переменной окружения."""
    value = os.getenv(env_var)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


# Токен для доступа к Yandex Music API
# Получите токен Яндекс Музыки здесь: https://github.com/MarshalX/yandex-music-api/discussions/513
YANDEX_MUSIC_TOKEN = os.getenv("YANDEX_MUSIC_TOKEN", "your_token_here")

# Директория для сохранения музыки
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "music")

# Качество аудио при скачивании
# Доступные значения:
#   "lossless" - без потерь (FLAC, ~1000 kbps) - максимальное качество
#   "hq"       - высокое качество (MP3 320 kbps) - рекомендуется
#   "nq"       - нормальное качество (MP3 192 kbps) - экономия места
AUDIO_QUALITY = os.getenv("AUDIO_QUALITY", "hq")

# Логирование
# Если LOGGING_ENABLED = True — логи пишутся в файл LOG_FILE
# Если False — логирование полностью отключено
LOGGING_ENABLED = _get_bool("LOGGING_ENABLED", True)
LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Кэширование метаданных
METADATA_CACHE_ENABLED = _get_bool("METADATA_CACHE_ENABLED", True)
METADATA_CACHE_FILE = os.getenv("METADATA_CACHE_FILE", "cache/metadata.json")
METADATA_CACHE_TTL_HOURS = _get_int("METADATA_CACHE_TTL_HOURS", 24)

# Многопоточность
# Количество одновременных загрузок (1 — без многопоточности)
MAX_CONCURRENT_DOWNLOADS = _get_int("MAX_CONCURRENT_DOWNLOADS", 4)