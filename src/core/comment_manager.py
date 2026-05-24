"""
Модуль генерации AI-комментариев.
Отправляет контекст в DeepSeek API и получает комментарии.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Callable, List, Optional

import httpx

logger = logging.getLogger(__name__)


# URL для API провайдеров
PROVIDER_URLS = {
    "deepseek": "https://api.deepseek.com/v1/chat/completions",
    "chatgpt": "https://api.openai.com/v1/chat/completions",
    "grok": "https://api.x.ai/v1/chat/completions",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
}

# Соответствие провайдеров и моделей
PROVIDER_MODELS = {
    "deepseek": "deepseek-chat",
    "chatgpt": "gpt-4o-mini",
    "grok": "grok-2-latest",
    "qwen": "qwen-turbo",
}


@dataclass
class CommentConfig:
    """Конфигурация генерации комментариев."""
    enabled: bool = True
    provider: str = "deepseek"  # deepseek, chatgpt, grok, qwen
    api_key: str = ""
    system_prompt: str = ""
    frequency: int = 5  # каждые N предложений
    max_retries: int = 3
    timeout: float = 60.0
    context_size: int = 5  # сколько предложений отправлять как контекст
    max_concurrent: int = 5  # макс. одновременных запросов к API


class CommentManager:
    """Менеджер генерации AI-комментариев.

    Пример использования:
        config = CommentConfig(
            provider="deepseek",
            api_key="sk-...",
            system_prompt="Ты — строгий критик...",
            frequency=5,
        )
        manager = CommentManager(config)
        comment = await manager.generate_comment("Текст контекста", 0, 0)
    """

    def __init__(self, config: CommentConfig):
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        """Ленивое создание HTTP-клиента."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.config.timeout,
                follow_redirects=True,
            )
        return self._client

    async def generate_comment(
        self,
        context: str,
        chapter_index: int,
        sentence_index: int,
    ) -> Optional[str]:
        """Генерация одного комментария.

        Args:
            context: Контекст (предыдущие предложения).
            chapter_index: Индекс главы.
            sentence_index: Индекс предложения.

        Returns:
            Текст комментария или None при ошибке.
        """
        if not self.config.api_key:
            logger.warning("API-ключ не задан, комментарий пропущен")
            return None

        if not self.config.system_prompt:
            logger.warning("Системный промпт не задан, комментарий пропущен")
            return None

        prompt = (
            f"Прокомментируй следующий отрывок из книги. "
            f"Дай очень короткий комментарий — 1-2 предложения, максимум 3:\n\n{context}"
        )

        for attempt in range(self.config.max_retries):
            try:
                comment = await self._call_api(prompt)
                if comment:
                    logger.debug(
                        "Комментарий получен: гл.%d, предл.%d, длина=%d",
                        chapter_index, sentence_index, len(comment),
                    )
                    return comment
            except httpx.TimeoutException:
                logger.warning(
                    "Таймаут API (попытка %d/%d): гл.%d, предл.%d",
                    attempt + 1, self.config.max_retries,
                    chapter_index, sentence_index,
                )
            except httpx.HTTPStatusError as e:
                logger.warning(
                    "Ошибка HTTP %s (попытка %d/%d): гл.%d, предл.%d",
                    e.response.status_code, attempt + 1,
                    self.config.max_retries,
                    chapter_index, sentence_index,
                )
            except httpx.ConnectError as e:
                logger.warning(
                    "Ошибка соединения с API (попытка %d/%d): %s — гл.%d, предл.%d",
                    attempt + 1, self.config.max_retries,
                    e.__class__.__name__,
                    chapter_index, sentence_index,
                )
            except httpx.RemoteProtocolError as e:
                logger.warning(
                    "Ошибка протокола API (попытка %d/%d): %s — гл.%d, предл.%d",
                    attempt + 1, self.config.max_retries,
                    e.__class__.__name__,
                    chapter_index, sentence_index,
                )
            except Exception as e:
                logger.warning(
                    "Неизвестная ошибка API (попытка %d/%d): [%s] %s — гл.%d, предл.%d",
                    attempt + 1, self.config.max_retries,
                    e.__class__.__name__, e,
                    chapter_index, sentence_index,
                )

            if attempt < self.config.max_retries - 1:
                wait = 2 ** attempt  # 1, 2, 4 секунды
                await asyncio.sleep(wait)

        logger.error(
            "Все попытки исчерпаны: гл.%d, предл.%d",
            chapter_index, sentence_index,
        )
        return None

    async def generate_all(
        self,
        sentences: List[str],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[Optional[str]]:
        """Генерация комментариев для всех групп предложений (конкурентно).

        Все запросы к API выполняются параллельно с ограничением
        max_concurrent (asyncio.Semaphore). Комментарии независимы —
        контекст строится только из исходных предложений.

        Args:
            sentences: Список предложений.
            progress_callback: Колбэк прогресса (текущий, всего).

        Returns:
            Список комментариев (None если не удалось сгенерировать).
        """
        freq = self.config.frequency
        total_groups = (len(sentences) + freq - 1) // freq

        if total_groups == 0:
            return []

        # Семафор для ограничения конкурентных запросов
        semaphore = asyncio.Semaphore(self.config.max_concurrent)
        completed = 0
        lock = asyncio.Lock()

        async def _generate_group(group_idx: int) -> Optional[str]:
            """Генерирует комментарий для одной группы с учётом семафора."""
            nonlocal completed

            async with semaphore:
                start = group_idx * freq
                end = min(start + freq, len(sentences))

                # Контекст: текущая группа + несколько предыдущих предложений
                context_start = max(0, start - self.config.context_size)
                context = " ".join(sentences[context_start:end])

                result = await self.generate_comment(
                    context=context,
                    chapter_index=0,
                    sentence_index=start,
                )

                # Безопасное обновление прогресса
                async with lock:
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, total_groups)

                return result

        # Запускаем все задачи конкурентно
        tasks = [_generate_group(i) for i in range(total_groups)]
        results = await asyncio.gather(*tasks)

        return list(results)

    async def _call_api(self, prompt: str) -> Optional[str]:
        """Вызов API провайдера."""
        client = self._get_client()
        url = PROVIDER_URLS.get(self.config.provider)
        model = PROVIDER_MODELS.get(self.config.provider)

        if not url or not model:
            logger.error("Неизвестный провайдер: %s", self.config.provider)
            return None

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": self.config.system_prompt},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 150,
            "temperature": 0.7,
        }

        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return content.strip()

    async def close(self):
        """Закрытие HTTP-клиента."""
        if self._client:
            await self._client.aclose()
            self._client = None
