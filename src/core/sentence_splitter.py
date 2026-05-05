"""
Модуль разбиения текста на предложения с учётом языка.
Поддерживает русский, английский, японский и китайский языки.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, Callable, List

logger = logging.getLogger(__name__)


class SentenceSplitter:
    """Разбиение текста на предложения с учётом языка.

    Для русского и английского использует spacy (если модель загружена),
    для японского и китайского — кастомные правила на основе регулярных выражений.
    """

    def __init__(self):
        self._splitters: Dict[str, Callable[[str], List[str]]] = {
            "ru": self._split_ru,
            "en": self._split_en,
            "ja": self._split_ja,
            "zh": self._split_zh,
        }
        self._nlp_ru = None
        self._nlp_en = None

    def split(self, text: str, lang: str = "ru") -> List[str]:
        """Разбиение текста на предложения.

        Args:
            text: Исходный текст.
            lang: Язык текста (ru, en, ja, zh).

        Returns:
            Список предложений.
        """
        if not text or not text.strip():
            return []

        splitter = self._splitters.get(lang, self._split_fallback)
        sentences = splitter(text)
        # Фильтр пустых и слишком коротких строк
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 1]
        return sentences

    def _load_spacy_ru(self):
        """Загрузка spacy модели для русского языка."""
        if self._nlp_ru is None:
            try:
                import spacy
                nlp = spacy.load("ru_core_news_sm")
                # Увеличиваем лимит длины текста: некоторые главы
                # "Братьев Карамазовых" >1M символов.
                # Для sentence-split'инга NER/parser не нужны,
                # поэтому высокий лимит безопасен.
                nlp.max_length = 10_000_000
                self._nlp_ru = nlp
                logger.info("Загружена spacy модель: ru_core_news_sm (max_length=10M)")
            except OSError:
                logger.warning(
                    "spacy модель ru_core_news_sm не найдена. "
                    "Установите: python -m spacy download ru_core_news_sm"
                )
                return False
        return True

    def _load_spacy_en(self):
        """Загрузка spacy модели для английского языка."""
        if self._nlp_en is None:
            try:
                import spacy
                nlp = spacy.load("en_core_web_sm")
                nlp.max_length = 10_000_000
                self._nlp_en = nlp
                logger.info("Загружена spacy модель: en_core_web_sm (max_length=10M)")
            except OSError:
                logger.warning(
                    "spacy модель en_core_web_sm не найдена. "
                    "Установите: python -m spacy download en_core_web_sm"
                )
                return False
        return True

    def _split_ru(self, text: str) -> List[str]:
        """Разбиение русского текста на предложения."""
        if self._load_spacy_ru():
            doc = self._nlp_ru(text)
            return [sent.text for sent in doc.sents]
        return self._split_fallback(text)

    def _split_en(self, text: str) -> List[str]:
        """Разбиение английского текста на предложения."""
        if self._load_spacy_en():
            doc = self._nlp_en(text)
            return [sent.text for sent in doc.sents]
        return self._split_fallback(text)

    def _split_ja(self, text: str) -> List[str]:
        """Разбиение японского текста на предложения.

        Японские знаки конца предложения: 。！？
        """
        # Используем позитивный просмотр вперёд для сохранения знака
        pattern = r'[^。！？\n]+[。！？]?'
        sentences = re.findall(pattern, text)
        return [s.strip() for s in sentences if s.strip()]

    def _split_zh(self, text: str) -> List[str]:
        """Разбиение китайского текста на предложения.

        Китайские знаки конца предложения: 。！？
        Также поддерживаются полуширинные !?
        """
        pattern = r'[^。！？!?\n]+[。！？!?]?'
        sentences = re.findall(pattern, text)
        return [s.strip() for s in sentences if s.strip()]

    def _split_fallback(self, text: str) -> List[str]:
        """Универсальное разбиение на предложения (резервный алгоритм).

        Используется, если spacy модель не загружена.
        """
        # Основной паттерн: ищем знаки конца предложения
        # с фильтрацией ложных срабатываний
        pattern = (
            r'(?<!\b[А-ЯA-Z][а-яa-z]{0,2})'  # Не после коротких слов (т.е., т.к.)
            r'(?<!\d\.\d)'                    # Не внутри чисел (2.0.1)
            r'(?<![А-ЯA-Z])\.(?!\w)'          # Не после инициалов
            r'|[.!?。！？\n]+(?=\s|$)'
        )
        # Упрощённый вариант: разбиваем по знакам конца предложения
        parts = re.split(r'(?<=[.!?。！？\n])\s+', text)
        result = []
        for part in parts:
            # Дополнительное разбиение по переносам строк
            sub_parts = [p.strip() for p in part.split("\n") if p.strip()]
            result.extend(sub_parts)
        return result
