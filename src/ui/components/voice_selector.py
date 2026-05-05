"""
Компонент выбора голоса TTS.
"""

from __future__ import annotations

from typing import Callable, List, Optional

import customtkinter as ctk


class VoiceSelector(ctk.CTkFrame):
    """Компонент выбора голоса из списка.

    Пример использования:
        selector = VoiceSelector(parent, "Голос текста:")
        selector.set_voices([{"name": "ru-RU-DariyaNeural", ...}])
        selected = selector.get_selected_voice()
    """

    def __init__(
        self,
        parent: ctk.CTkFrame,
        label: str = "Голос:",
        default_voice: str = "",
        on_change: Optional[Callable] = None,
    ):
        super().__init__(parent)
        self.on_change = on_change
        self.voices: List[dict] = []

        ctk.CTkLabel(
            self,
            text=label,
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=(0, 10))

        self.voice_var = ctk.StringVar(value=default_voice)
        self.voice_menu = ctk.CTkOptionMenu(
            self,
            values=[default_voice] if default_voice else ["Нет голосов"],
            variable=self.voice_var,
            command=self._on_change,
            width=250,
        )
        self.voice_menu.pack(side="left")

    def set_voices(self, voices: List[dict]):
        """Установка списка доступных голосов.

        Args:
            voices: Список словарей с информацией о голосах.
        """
        self.voices = voices
        voice_names = [v["name"] for v in voices]
        if voice_names:
            self.voice_menu.configure(values=voice_names)
            if not self.voice_var.get() or self.voice_var.get() not in voice_names:
                self.voice_var.set(voice_names[0])

    def get_selected_voice(self) -> str:
        """Получение выбранного голоса.

        Returns:
            Имя выбранного голоса.
        """
        return self.voice_var.get()

    def _on_change(self, value: str):
        """Обработчик изменения выбора."""
        if self.on_change:
            self.on_change(value)
