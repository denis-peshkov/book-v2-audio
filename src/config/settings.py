"""
Модуль управления настройками приложения.
Загрузка и сохранение конфигурации в TOML-файл.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import tomllib as tomli
import tomli_w

logger = logging.getLogger(__name__)

# Путь по умолчанию для файла настроек
DEFAULT_CONFIG_DIR = Path.home() / ".audiobook-generator"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "settings.toml"


@dataclass
class Settings:
    """Настройки приложения."""
    # Язык
    ui_lang: str = "ru"
    book_lang: str = "ru"

    # AI-провайдер
    ai_provider: str = "deepseek"

    # TTS бэкенд
    tts_backend: str = "edge"  # "edge" | "piper"

    # Голоса TTS
    main_voice: str = "ru-RU-SvetlanaNeural"
    comment_voice: str = "ru-RU-DmitryNeural"
    main_speed: float = 1.0
    comment_speed: float = 1.0

    # Паузы
    pause_before_comment: float = 1.0
    pause_after_comment: float = 0.7
    pause_between_sentences: float = 0.3
    chapter_pause: float = 1.5

    # Комментарии
    comment_frequency: int = 5
    max_concurrent: int = 5
    system_prompt: str = ""

    # Пути
    output_dir: str = str(Path.home() / "audiobooks")
    book_path: str = ""

    # Окно
    window_width: int = 800
    window_height: int = 600

    # Первый запуск
    first_run: bool = True

    # Диапазон глав (0 = все)
    chapter_start: int = 0
    chapter_end: int = 0


# Маппинг старых (несуществующих) голосов на новые
_VOICE_MIGRATION = {
    "ru-RU-DariyaNeural": "ru-RU-SvetlanaNeural",
    "ru-RU-MaxNeural": "ru-RU-DmitryNeural",
}


def _migrate_voices(settings: Settings) -> Settings:
    """Миграция устаревших голосов на актуальные.

    Microsoft Edge TTS изменил список доступных голосов.
    DariyaNeural и MaxNeural больше не существуют.
    """
    if settings.main_voice in _VOICE_MIGRATION:
        logger.info(
            "Миграция голоса: %s → %s",
            settings.main_voice, _VOICE_MIGRATION[settings.main_voice],
        )
        settings.main_voice = _VOICE_MIGRATION[settings.main_voice]
    if settings.comment_voice in _VOICE_MIGRATION:
        logger.info(
            "Миграция голоса: %s → %s",
            settings.comment_voice, _VOICE_MIGRATION[settings.comment_voice],
        )
        settings.comment_voice = _VOICE_MIGRATION[settings.comment_voice]
    return settings


def load_settings(config_path: Optional[Path] = None) -> Settings:
    """Загрузка настроек из TOML-файла.

    Args:
        config_path: Путь к файлу настроек. По умолчанию ~/.audiobook-generator/settings.toml.

    Returns:
        Объект Settings с загруженными настройками.
    """
    path = config_path or DEFAULT_CONFIG_PATH

    if not path.exists():
        logger.info("Файл настроек не найден: %s, используются настройки по умолчанию", path)
        return Settings()

    try:
        with open(path, "rb") as f:
            data = tomli.load(f)

        # Фильтруем только известные поля
        known_fields = {k for k in asdict(Settings())}
        filtered_data = {k: v for k, v in data.items() if k in known_fields}

        settings = Settings(**filtered_data)
        settings = _migrate_voices(settings)
        logger.info("Настройки загружены: %s", path)
        return settings

    except (tomli.TOMLDecodeError, IOError, TypeError) as e:
        logger.warning("Ошибка загрузки настроек: %s", e)
        return Settings()


def save_settings(settings: Settings, config_path: Optional[Path] = None) -> None:
    """Сохранение настроек в TOML-файл.

    Args:
        settings: Объект Settings для сохранения.
        config_path: Путь к файлу настроек. По умолчанию ~/.audiobook-generator/settings.toml.
    """
    path = config_path or DEFAULT_CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    data = asdict(settings)

    try:
        with open(path, "wb") as f:
            tomli_w.dump(data, f)
        logger.info("Настройки сохранены: %s", path)
    except (IOError, TypeError) as e:
        logger.error("Ошибка сохранения настроек: %s", e)
