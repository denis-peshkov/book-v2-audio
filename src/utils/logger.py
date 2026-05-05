"""
Модуль настройки логирования.
Использует structlog для структурированных логов.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
    console: bool = True,
) -> None:
    """Настройка логирования.

    Args:
        log_file: Путь к файлу лога. Если None, лог в файл не пишется.
        level: Уровень логирования.
        console: Писать ли логи в консоль.
    """
    handlers = []

    if console:
        # В --windowed сборке PyInstaller sys.stdout может быть None
        stdout = sys.stdout
        if stdout is not None:
            console_handler = logging.StreamHandler(stdout)
            console_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                    datefmt="%H:%M:%S",
                )
            )
            handlers.append(console_handler)

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        handlers.append(file_handler)

    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True,
    )

    # Тихие логи для библиотек
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("edge_tts").setLevel(logging.WARNING)
    logging.getLogger("pydub").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info("Логирование настроено: уровень=%s, файл=%s", 
                logging.getLevelName(level), log_file)
