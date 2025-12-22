def sanitize_filename(filename):
    """Очищает имя файла от недопустимых символов"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()


def detect_audio_format(file_path):
    """Определяет формат аудио файла по сигнатурам"""
    with open(file_path, 'rb') as f:
        header = f.read(12)

    if header[:3] == b'ID3' or (len(header) > 2 and header[0] == 0xFF and (header[1] & 0xE0) == 0xE0):
        return '.mp3'
    if len(header) > 12 and header[4:8] == b'ftyp':
        return '.m4a'
    if header[:4] == b'fLaC':
        return '.flac'
    if header[:4] == b'OggS':
        return '.ogg'

    return '.mp3'