import logging
import os


def setup_logging(config) -> None:
    """Настраивает логирование в файл по настройкам из config."""
    # Полностью отключаем логирование, если выключено в конфиге
    if not getattr(config, "LOGGING_ENABLED", False):
        logging.disable(logging.CRITICAL)
        return

    logging.disable(logging.NOTSET)

    log_file = getattr(config, "LOG_FILE", "app.log")
    log_level_name = getattr(config, "LOG_LEVEL", "INFO")
    log_level = getattr(logging, log_level_name.upper(), logging.INFO)

    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.FileHandler(log_file, encoding="utf-8")],
        force=True,  # гарантируем отсутствие вывода в консоль
    )

    # Урезаем шум от внешних библиотек
    logging.getLogger("yandex_music").setLevel(logging.WARNING)
