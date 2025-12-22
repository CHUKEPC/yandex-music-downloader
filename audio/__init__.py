"""
Обработка аудио файлов
"""

from .audio_processor import AudioProcessor, UnsupportedAudioFormatError

__all__ = ['AudioProcessor', 'UnsupportedAudioFormatError']