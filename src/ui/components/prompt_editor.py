"""
Компонент редактора системного промпта.
"""

from __future__ import annotations

from typing import Optional

import customtkinter as ctk


class PromptEditor(ctk.CTkFrame):
    """Редактор системного промпта с предустановленными шаблонами.

    Пример использования:
        editor = PromptEditor(parent)
        editor.set_prompts({"critic": "Ты — критик...", "fan": "Ты — фанат..."})
        prompt = editor.get_prompt()
    """

    def __init__(
        self,
        parent: ctk.CTkFrame,
        label: str = "Системный промпт:",
        height: int = 120,
    ):
        super().__init__(parent)
        self.height = height

        ctk.CTkLabel(
            self,
            text=label,
            font=ctk.CTkFont(size=13),
        ).pack(anchor="w", padx=5, pady=(5, 5))

        self.prompt_text = ctk.CTkTextbox(self, height=height)
        self.prompt_text.pack(fill="x", padx=5, pady=(0, 5))

    def set_prompt(self, text: str):
        """Установка текста промпта.

        Args:
            text: Текст промпта.
        """
        self.prompt_text.delete("1.0", "end")
        self.prompt_text.insert("1.0", text)

    def get_prompt(self) -> str:
        """Получение текста промпта.

        Returns:
            Текст промпта.
        """
        return self.prompt_text.get("1.0", "end-1c").strip()

    def clear(self):
        """Очистка текста промпта."""
        self.prompt_text.delete("1.0", "end")
