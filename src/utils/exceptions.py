"""
Кастомные исключения приложения.
"""


class AudiobookError(Exception):
    """Базовое исключение приложения."""
    pass


class FB2ParseError(AudiobookError):
    """Ошибка парсинга FB2-файла."""
    pass


class TTSGenerationError(AudiobookError):
    """Ошибка синтеза речи."""
    pass


class CommentGenerationError(AudiobookError):
    """Ошибка генерации комментария."""
    pass


class AudioAssemblyError(AudiobookError):
    """Ошибка склейки аудио."""
    pass


class PipelineCanceledError(AudiobookError):
    """Процесс создания аудиокниги был отменён."""
    pass
