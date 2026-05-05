"""
Модуль сохранения прогресса (чекпоинты).
Позволяет продолжить генерацию после сбоя или закрытия приложения.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Checkpoint:
    """Точка сохранения прогресса."""
    book_path: str
    last_completed_chapter: int
    total_chapters: int
    config_hash: str  # хеш настроек для проверки неизменности
    timestamp: float  # время сохранения
    output_dir: str = ""  # директория с временными файлами


class CheckpointManager:
    """Менеджер чекпоинтов.

    Сохраняет прогресс после каждой главы, позволяет восстановиться после сбоя.

    Пример использования:
        manager = CheckpointManager(Path.home() / ".audiobook-generator")
        manager.save(Checkpoint(
            book_path="/path/to/book.fb2",
            last_completed_chapter=3,
            total_chapters=10,
            config_hash="abc123",
            timestamp=time.time(),
        ))
        cp = manager.load()  # Checkpoint или None
    """

    CHECKPOINT_FILENAME = "checkpoint.json"

    def __init__(self, work_dir: Path):
        self.work_dir = work_dir
        self.checkpoint_path = work_dir / self.CHECKPOINT_FILENAME

    def save(self, checkpoint: Checkpoint) -> None:
        """Сохранение чекпоинта.

        Args:
            checkpoint: Данные для сохранения.
        """
        self.work_dir.mkdir(parents=True, exist_ok=True)

        data = asdict(checkpoint)
        data["timestamp"] = datetime.now().timestamp()

        with open(self.checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(
            "Чекпоинт сохранён: глава %d/%d, книга: %s",
            checkpoint.last_completed_chapter,
            checkpoint.total_chapters,
            checkpoint.book_path,
        )

    def load(self) -> Optional[Checkpoint]:
        """Загрузка чекпоинта.

        Returns:
            Checkpoint или None, если чекпоинта нет.
        """
        if not self.checkpoint_path.exists():
            return None

        try:
            with open(self.checkpoint_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Checkpoint(**data)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning("Ошибка загрузки чекпоинта: %s", e)
            return None

    def clear(self) -> None:
        """Очистка чекпоинта (после успешного завершения)."""
        if self.checkpoint_path.exists():
            self.checkpoint_path.unlink()
            logger.info("Чекпоинт очищен")

    def has_checkpoint(self) -> bool:
        """Проверка наличия чекпоинта.

        Returns:
            True если чекпоинт существует.
        """
        return self.checkpoint_path.exists()

    @staticmethod
    def compute_config_hash(config: dict) -> str:
        """Вычисление хеша конфигурации для проверки неизменности.

        Args:
            config: Словарь с настройками.

        Returns:
            SHA256 хеш конфигурации.
        """
        config_str = json.dumps(config, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]
