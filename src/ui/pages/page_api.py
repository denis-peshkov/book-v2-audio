"""
Шаг 2: Выбор AI-провайдера и ввод API-ключа.
"""

from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from src.config.settings import Settings
from src.config.key_manager import KeyManager

# Тексты на разных языках
API_TEXTS = {
    "ru": {
        "title": "Шаг 2: AI-провайдер и API-ключ",
        "desc": "Выберите провайдера для генерации AI-комментариев.\nЕсли комментарии не нужны — просто нажмите «Далее», ключ не обязателен.",
        "provider_label": "AI-провайдер:",
        "key_label": "API-ключ:",
        "key_placeholder": "Введите API-ключ...",
        "show_key": "Показать ключ",
        "info": "Ключ будет сохранён в системном хранилище паролей (keyring)\n"
                "и не будет отображаться в открытом виде в конфигурационных файлах",
    },
    "en": {
        "title": "Step 2: AI Provider & API Key",
        "desc": "Select provider for AI comment generation.\nIf you don't need comments — just click «Next», the key is optional.",
        "provider_label": "AI Provider:",
        "key_label": "API Key:",
        "key_placeholder": "Enter API key...",
        "show_key": "Show key",
        "info": "The key will be saved in the system keyring\n"
                "and will not be visible in configuration files",
    },
    "ja": {
        "title": "ステップ2: AIプロバイダーとAPIキー",
        "desc": "AIコメント生成のプロバイダーを選択します。\nコメントが不要な場合は「次へ」をクリックしてください。キーは必須ではありません。",
        "provider_label": "AIプロバイダー:",
        "key_label": "APIキー:",
        "key_placeholder": "APIキーを入力...",
        "show_key": "キーを表示",
        "info": "キーはシステムキーリングに保存され\n設定ファイルで表示されることはありません",
    },
    "zh": {
        "title": "步骤2：AI提供商和API密钥",
        "desc": "选择用于生成AI评论的提供商。\n如果不需要评论，只需点击「下一步」，密钥不是必需的。",
        "provider_label": "AI提供商：",
        "key_label": "API密钥：",
        "key_placeholder": "输入API密钥...",
        "show_key": "显示密钥",
        "info": "密钥将保存在系统密钥环中\n不会在配置文件中以明文显示",
    },
}


class PageAPI(ctk.CTkFrame):
    """Страница выбора AI-провайдера и ввода API-ключа."""

    PROVIDERS = [
        ("DeepSeek", "deepseek"),
        ("ChatGPT (OpenAI)", "chatgpt"),
        ("Grok (xAI)", "grok"),
        ("Qwen (Alibaba)", "qwen"),
    ]

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
        t = API_TEXTS.get(lang, API_TEXTS["ru"])

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

        # Выбор провайдера
        provider_frame = ctk.CTkFrame(self)
        provider_frame.pack(fill="x", padx=40, pady=10)

        ctk.CTkLabel(
            provider_frame,
            text=t["provider_label"],
            font=ctk.CTkFont(size=14),
        ).pack(anchor="w", padx=10, pady=(10, 5))

        self.provider_var = ctk.StringVar(
            value=self._get_provider_display(self.settings.ai_provider)
        )
        provider_menu = ctk.CTkOptionMenu(
            provider_frame,
            values=[p[0] for p in self.PROVIDERS],
            variable=self.provider_var,
        )
        provider_menu.pack(anchor="w", padx=10, pady=(0, 10))

        # API-ключ
        key_frame = ctk.CTkFrame(self)
        key_frame.pack(fill="x", padx=40, pady=10)

        ctk.CTkLabel(
            key_frame,
            text=t["key_label"],
            font=ctk.CTkFont(size=14),
        ).pack(anchor="w", padx=10, pady=(10, 5))

        self.key_entry = ctk.CTkEntry(
            key_frame,
            placeholder_text=t["key_placeholder"],
            show="*",  # скрытый ввод
            width=400,
        )
        self.key_entry.pack(anchor="w", padx=10, pady=(0, 5))

        # Кнопка показать/скрыть ключ
        self.show_key_var = ctk.BooleanVar(value=False)
        show_key_btn = ctk.CTkCheckBox(
            key_frame,
            text=t["show_key"],
            variable=self.show_key_var,
            command=self._toggle_key_visibility,
        )
        show_key_btn.pack(anchor="w", padx=10, pady=(0, 10))

        # Информация
        info = ctk.CTkLabel(
            self,
            text=t["info"],
            font=ctk.CTkFont(size=12),
            text_color="gray",
            justify="left",
        )
        info.pack(pady=(20, 10))

    def _get_provider_display(self, code: str) -> str:
        """Получение отображаемого названия провайдера."""
        for display, value in self.PROVIDERS:
            if value == code:
                return display
        return "DeepSeek"

    def _toggle_key_visibility(self):
        """Переключение видимости API-ключа."""
        if self.show_key_var.get():
            self.key_entry.configure(show="")
        else:
            self.key_entry.configure(show="*")

    def set_api_key(self, key: str):
        """Установка API-ключа (из сохранённого)."""
        self.key_entry.delete(0, "end")
        self.key_entry.insert(0, key)

    def get_data(self) -> dict:
        """Сбор данных со страницы."""
        provider_display = self.provider_var.get()
        provider_code = ""
        for display, code in self.PROVIDERS:
            if display == provider_display:
                provider_code = code
                break

        api_key = self.key_entry.get().strip()

        # Сохраняем ключ
        if api_key:
            KeyManager.save_key(provider_code, api_key)

        return {
            "ai_provider": provider_code,
        }

    def validate(self) -> bool:
        """Валидация данных страницы."""
        api_key = self.key_entry.get().strip()
        if not api_key:
            # Показываем предупреждение, но не блокируем
            # (пользователь может ввести ключ позже)
            return True
        if len(api_key) < 10:
            return False
        return True
