"""
Шаг 1: Выбор языка интерфейса и языка книг.
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

import customtkinter as ctk

from src.config.settings import Settings

logger = logging.getLogger(__name__)

# Отображаемые названия языков → код языка
LANG_MAP = {
    "Русский": "ru",
    "English": "en",
    "日本語": "ja",
    "中文": "zh",
}

# Код языка → отображаемое название
DISPLAY_MAP = {v: k for k, v in LANG_MAP.items()}


class PageLanguage(ctk.CTkFrame):
    """Страница выбора языка."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        settings: Settings,
        on_complete: Optional[Callable] = None,
        on_lang_change: Optional[Callable[[str], None]] = None,
    ):
        super().__init__(parent)
        self.settings = settings
        self.on_complete = on_complete
        self.on_lang_change = on_lang_change

        # Ссылки на виджеты для обновления языка
        self._title_label: Optional[ctk.CTkLabel] = None
        self._desc_label: Optional[ctk.CTkLabel] = None
        self._ui_label: Optional[ctk.CTkLabel] = None
        self._book_label: Optional[ctk.CTkLabel] = None
        self._info_label: Optional[ctk.CTkLabel] = None

        self._create_widgets()

    def _create_widgets(self):
        """Создание виджетов страницы."""
        # Заголовок
        self._title_label = ctk.CTkLabel(
            self,
            text="Шаг 1: Выбор языка",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self._title_label.pack(pady=(20, 10))

        self._desc_label = ctk.CTkLabel(
            self,
            text="Выберите язык интерфейса и язык книг для озвучки",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        self._desc_label.pack(pady=(0, 20))

        # Язык интерфейса
        ui_frame = ctk.CTkFrame(self)
        ui_frame.pack(fill="x", padx=40, pady=10)

        self._ui_label = ctk.CTkLabel(
            ui_frame,
            text="Язык интерфейса:",
            font=ctk.CTkFont(size=14),
        )
        self._ui_label.pack(anchor="w", padx=10, pady=(10, 5))

        self.ui_lang_var = ctk.StringVar(
            value=DISPLAY_MAP.get(self.settings.ui_lang, "Русский")
        )
        self.ui_lang_menu = ctk.CTkOptionMenu(
            ui_frame,
            values=list(LANG_MAP.keys()),
            variable=self.ui_lang_var,
            command=self._on_ui_lang_change,
        )
        self.ui_lang_menu.pack(anchor="w", padx=10, pady=(0, 10))

        # Язык книг
        book_frame = ctk.CTkFrame(self)
        book_frame.pack(fill="x", padx=40, pady=10)

        self._book_label = ctk.CTkLabel(
            book_frame,
            text="Язык книг:",
            font=ctk.CTkFont(size=14),
        )
        self._book_label.pack(anchor="w", padx=10, pady=(10, 5))

        self.book_lang_var = ctk.StringVar(
            value=DISPLAY_MAP.get(self.settings.book_lang, "Русский")
        )
        self.book_lang_menu = ctk.CTkOptionMenu(
            book_frame,
            values=list(LANG_MAP.keys()),
            variable=self.book_lang_var,
            command=self._on_book_lang_change,
        )
        self.book_lang_menu.pack(anchor="w", padx=10, pady=(0, 10))

        # Пояснение
        self._info_label = ctk.CTkLabel(
            self,
            text="Язык книг влияет на то, как текст разбивается на предложения\n"
                 "и какие голоса TTS будут предложены по умолчанию",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            justify="left",
        )
        self._info_label.pack(pady=(20, 10))

    def _on_ui_lang_change(self, value: str):
        """Обработчик смены языка интерфейса — сразу меняет UI."""
        lang_code = LANG_MAP.get(value, "ru")
        self.settings.ui_lang = lang_code

        # Меняем тексты в интерфейсе
        self._apply_ui_language(lang_code)

        # Уведомляем wizard и app об изменении языка
        if self.on_lang_change:
            self.on_lang_change(lang_code)

    def _on_book_lang_change(self, value: str):
        """Обработчик смены языка книг — обновляет язык, голоса подберутся по полу."""
        lang_code = LANG_MAP.get(value, "ru")
        self.settings.book_lang = lang_code

        logger.info(
            "Язык книг изменён на %s (голоса определяются по полу и движку при запуске)",
            lang_code,
        )

    def _apply_ui_language(self, lang_code: str):
        """Применение языка интерфейса — смена текстов на странице."""
        # Тексты для каждого языка
        texts = {
            "ru": {
                "title": "Шаг 1: Выбор языка",
                "desc": "Выберите язык интерфейса и язык книг для озвучки",
                "ui_label": "Язык интерфейса:",
                "book_label": "Язык книг:",
                "info": "Язык книг влияет на то, как текст разбивается на предложения\n"
                        "и какие голоса TTS будут предложены по умолчанию",
            },
            "en": {
                "title": "Step 1: Language Selection",
                "desc": "Select interface language and book language for narration",
                "ui_label": "Interface language:",
                "book_label": "Book language:",
                "info": "Book language affects how text is split into sentences\n"
                        "and which TTS voices are suggested by default",
            },
            "ja": {
                "title": "ステップ1: 言語選択",
                "desc": "インターフェース言語とナレーションの言語を選択してください",
                "ui_label": "インターフェース言語:",
                "book_label": "書籍の言語:",
                "info": "書籍の言語は文章の分割方法と\n"
                        "デフォルトのTTS音声に影響します",
            },
            "zh": {
                "title": "步骤1：语言选择",
                "desc": "选择界面语言和用于朗读的书籍语言",
                "ui_label": "界面语言：",
                "book_label": "书籍语言：",
                "info": "书籍语言影响文本如何分割成句子\n"
                        "以及默认推荐的TTS语音",
            },
        }

        t = texts.get(lang_code, texts["ru"])

        # Обновляем тексты через сохранённые ссылки на виджеты
        if self._title_label:
            self._title_label.configure(text=t["title"])
        if self._desc_label:
            self._desc_label.configure(text=t["desc"])
        if self._ui_label:
            self._ui_label.configure(text=t["ui_label"])
        if self._book_label:
            self._book_label.configure(text=t["book_label"])
        if self._info_label:
            self._info_label.configure(text=t["info"])

    def get_data(self) -> dict:
        """Сбор данных со страницы."""
        return {
            "ui_lang": LANG_MAP.get(self.ui_lang_var.get(), "ru"),
            "book_lang": LANG_MAP.get(self.book_lang_var.get(), "ru"),
        }

    def validate(self) -> bool:
        """Валидация данных страницы."""
        return True
