"""
Шаг 3: Отображение логотипа приложения.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk

from src.config.settings import Settings

# Тексты на разных языках
LOGO_TEXTS = {
    "ru": {
        "title": "Добро пожаловать!",
        "app_name": "Audiobook Generator",
        "desc": "Создавайте аудиокниги из FB2-файлов\n"
                "с AI-комментариями и синтезом речи Microsoft Edge",
        "info": "Нажмите «Далее», чтобы продолжить настройку",
    },
    "en": {
        "title": "Welcome!",
        "app_name": "Audiobook Generator",
        "desc": "Create audiobooks from FB2 files\n"
                "with AI commentary and Microsoft Edge TTS",
        "info": "Click «Next» to continue setup",
    },
    "ja": {
        "title": "ようこそ！",
        "app_name": "Audiobook Generator",
        "desc": "FB2ファイルからAIコメントと\nMicrosoft Edge TTSでオーディオブックを作成",
        "info": "「次へ」をクリックして設定を続ける",
    },
    "zh": {
        "title": "欢迎！",
        "app_name": "Audiobook Generator",
        "desc": "从FB2文件创建有声书\n带有AI评论和Microsoft Edge语音合成",
        "info": "点击「下一步」继续设置",
    },
}


class PageLogo(ctk.CTkFrame):
    """Страница с логотипом приложения."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        settings: Settings,
        on_complete: Optional[Callable] = None,
    ):
        super().__init__(parent)
        self.settings = settings
        self.on_complete = on_complete

        self._create_widgets()

    def _create_widgets(self):
        """Создание виджетов страницы."""
        lang = self.settings.ui_lang
        t = LOGO_TEXTS.get(lang, LOGO_TEXTS["ru"])

        # Заголовок
        title = ctk.CTkLabel(
            self,
            text=t["title"],
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.pack(pady=(30, 10))

        # Попытка загрузить логотип
        logo_path = self._find_logo()
        if logo_path:
            try:
                from PIL import Image
                logo_image = ctk.CTkImage(
                    light_image=Image.open(logo_path),
                    dark_image=Image.open(logo_path),
                    size=(200, 200),
                )
                logo_label = ctk.CTkLabel(self, image=logo_image, text="")
                logo_label.pack(pady=20)
            except Exception:
                pass

        # Название приложения
        app_name = ctk.CTkLabel(
            self,
            text=t["app_name"],
            font=ctk.CTkFont(size=18),
        )
        app_name.pack(pady=(10, 5))

        # Описание
        desc = ctk.CTkLabel(
            self,
            text=t["desc"],
            font=ctk.CTkFont(size=13),
            text_color="gray",
            justify="center",
        )
        desc.pack(pady=(5, 20))

        # Инфо о продолжении
        info = ctk.CTkLabel(
            self,
            text=t["info"],
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        info.pack(pady=(20, 10))

    def _find_logo(self) -> Optional[Path]:
        """Поиск файла логотипа."""
        # Пути поиска (включая корень проекта и PyInstaller bundle)
        base = Path(getattr(sys, '_MEIPASS', '.'))
        paths = [
            base / "logo.png",                    # корень проекта / bundle
            Path("logo.png"),
            Path("resources/logo.png"),
            Path("../resources/logo.png"),
            Path.home() / ".audiobook-generator" / "logo.png",
        ]
        for p in paths:
            if p.exists():
                return p
        return None

    def get_data(self) -> dict:
        """Сбор данных со страницы."""
        return {}

    def validate(self) -> bool:
        """Валидация данных страницы."""
        return True
