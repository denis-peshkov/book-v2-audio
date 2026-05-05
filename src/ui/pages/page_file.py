"""
Шаг 4: Загрузка FB2-файла и отображение метаданных.
"""

from __future__ import annotations

import logging
from pathlib import Path
from tkinter import filedialog
from typing import Callable, Optional

import customtkinter as ctk

from src.config.settings import Settings
from src.core.fb2_parser import FB2Parser

logger = logging.getLogger(__name__)

# Тексты на разных языках
FILE_TEXTS = {
    "ru": {
        "title": "Шаг 4: Загрузка FB2-файла",
        "desc": "Выберите FB2-файл книги для озвучки",
        "select_btn": "Выбрать FB2-файл...",
        "no_file": "Файл не выбран",
        "title_label": "Название:",
        "author_label": "Автор:",
        "chapters_label": "Глав:",
        "lang_label": "Язык:",
        "unknown": "Неизвестно",
        "parse_error": "Ошибка парсинга файла:",
    },
    "en": {
        "title": "Step 4: Load FB2 File",
        "desc": "Select an FB2 book file for narration",
        "select_btn": "Select FB2 file...",
        "no_file": "No file selected",
        "title_label": "Title:",
        "author_label": "Author:",
        "chapters_label": "Chapters:",
        "lang_label": "Language:",
        "unknown": "Unknown",
        "parse_error": "File parsing error:",
    },
    "ja": {
        "title": "ステップ4: FB2ファイルの読み込み",
        "desc": "ナレーション用のFB2ファイルを選択してください",
        "select_btn": "FB2ファイルを選択...",
        "no_file": "ファイルが選択されていません",
        "title_label": "タイトル:",
        "author_label": "著者:",
        "chapters_label": "章数:",
        "lang_label": "言語:",
        "unknown": "不明",
        "parse_error": "ファイル解析エラー:",
    },
    "zh": {
        "title": "步骤4：加载FB2文件",
        "desc": "选择用于朗读的FB2书籍文件",
        "select_btn": "选择FB2文件...",
        "no_file": "未选择文件",
        "title_label": "标题：",
        "author_label": "作者：",
        "chapters_label": "章节数：",
        "lang_label": "语言：",
        "unknown": "未知",
        "parse_error": "文件解析错误：",
    },
}


class PageFile(ctk.CTkFrame):
    """Страница загрузки FB2-файла."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        settings: Settings,
        on_complete: Optional[Callable] = None,
    ):
        super().__init__(parent)
        self.settings = settings
        self.on_complete = on_complete
        self.book_path: Optional[Path] = None
        self.book_metadata: Optional[dict] = None

        self._create_widgets()

    def _create_widgets(self):
        """Создание виджетов страницы."""
        lang = self.settings.ui_lang
        t = FILE_TEXTS.get(lang, FILE_TEXTS["ru"])

        # Заголовок
        title = ctk.CTkLabel(
            self,
            text=t["title"],
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        title.pack(pady=(20, 10))

        desc = ctk.CTkLabel(
            self,
            text=t["desc"],
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        desc.pack(pady=(0, 20))

        # Кнопка выбора файла
        self.file_frame = ctk.CTkFrame(self)
        self.file_frame.pack(fill="x", padx=40, pady=10)

        self.select_btn = ctk.CTkButton(
            self.file_frame,
            text=t["select_btn"],
            command=self._select_file,
            width=200,
        )
        self.select_btn.pack(pady=15)

        # Информация о выбранном файле
        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.pack(fill="x", padx=40, pady=10)

        self.file_path_label = ctk.CTkLabel(
            self.info_frame,
            text=t["no_file"],
            font=ctk.CTkFont(size=13),
            text_color="gray",
            wraplength=500,
        )
        self.file_path_label.pack(anchor="w", padx=10, pady=(10, 5))

        # Метаданные
        self.meta_frame = ctk.CTkFrame(self.info_frame)
        self.meta_frame.pack(fill="x", padx=10, pady=(5, 10))

        self.meta_title_label = ctk.CTkLabel(
            self.meta_frame,
            text="",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.meta_title_label.pack(anchor="w", padx=5, pady=2)

        self.meta_author_label = ctk.CTkLabel(
            self.meta_frame,
            text="",
            font=ctk.CTkFont(size=13),
        )
        self.meta_author_label.pack(anchor="w", padx=5, pady=2)

        self.meta_chapters_label = ctk.CTkLabel(
            self.meta_frame,
            text="",
            font=ctk.CTkFont(size=13),
        )
        self.meta_chapters_label.pack(anchor="w", padx=5, pady=2)

        self.meta_lang_label = ctk.CTkLabel(
            self.meta_frame,
            text="",
            font=ctk.CTkFont(size=13),
        )
        self.meta_lang_label.pack(anchor="w", padx=5, pady=2)

        # Скрываем метаданные до выбора файла
        self.meta_frame.pack_forget()

    def _select_file(self):
        """Открытие диалога выбора файла."""
        filename = filedialog.askopenfilename(
            title="Выберите FB2-файл",
            filetypes=[("FB2 files", "*.fb2"), ("All files", "*.*")],
        )
        if not filename:
            return

        path = Path(filename)
        if not path.exists():
            return

        self.book_path = path
        self.file_path_label.configure(text=str(path))

        # Парсим метаданные
        try:
            parser = FB2Parser()
            book = parser.parse(path)
            lang = self.settings.ui_lang
            t = FILE_TEXTS.get(lang, FILE_TEXTS["ru"])
            self.book_metadata = {
                "title": book.metadata.title or t["unknown"],
                "author": book.metadata.author or t["unknown"],
                "chapters": len(book.chapters),
                "lang": book.metadata.lang,
            }

            # Отображаем метаданные
            self.meta_title_label.configure(
                text=f"{t['title_label']} {self.book_metadata['title']}"
            )
            self.meta_author_label.configure(
                text=f"{t['author_label']} {self.book_metadata['author']}"
            )
            self.meta_chapters_label.configure(
                text=f"{t['chapters_label']} {self.book_metadata['chapters']}"
            )
            lang_display = {
                "ru": "Русский", "en": "English",
                "ja": "日本語", "zh": "中文",
            }.get(self.book_metadata["lang"], self.book_metadata["lang"])
            self.meta_lang_label.configure(
                text=f"Язык: {lang_display}"
            )

            self.meta_frame.pack(fill="x", padx=10, pady=(5, 10))

            logger.info(
                "Выбран файл: %s (%s, %d глав)",
                path, book.metadata.title, len(book.chapters),
            )

        except Exception as e:
            logger.error("Ошибка парсинга FB2: %s", e)
            lang = self.settings.ui_lang
            t = FILE_TEXTS.get(lang, FILE_TEXTS["ru"])
            self.meta_title_label.configure(
                text=f"{t['parse_error']} {e}",
                text_color="red",
            )
            self.meta_frame.pack(fill="x", padx=10, pady=(5, 10))

    def get_data(self) -> dict:
        """Сбор данных со страницы."""
        return {
            "book_path": str(self.book_path) if self.book_path else "",
        }

    def validate(self) -> bool:
        """Валидация данных страницы."""
        if not self.book_path:
            return False
        return True
