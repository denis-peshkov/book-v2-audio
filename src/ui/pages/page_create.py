"""
Шаг 8: Создание аудиокниги — прогресс внутри визарда (не модальное окно).
"""

from __future__ import annotations

import logging
import time
import tkinter
from typing import Callable, Optional

import customtkinter as ctk

from src.config.settings import Settings
from src.utils.scope_display import (
    STAGE_PREPARE,
    STAGE_SYNTH,
    STAGE_LABELS,
)

logger = logging.getLogger(__name__)

CREATE_TEXTS = {
    "ru": {
        "title": "Создание аудиокниги",
        "pause": "⏸ Пауза",
        "resume": "▶ Продолжить",
        "cancel": "✕ Отмена",
    },
    "en": {
        "title": "Creating audiobook",
        "pause": "⏸ Pause",
        "resume": "▶ Resume",
        "cancel": "✕ Cancel",
    },
    "ja": {
        "title": "オーディオブック作成",
        "pause": "⏸ 一時停止",
        "resume": "▶ 再開",
        "cancel": "✕ キャンセル",
    },
    "zh": {
        "title": "正在创建有声书",
        "pause": "⏸ 暂停",
        "resume": "▶ 继续",
        "cancel": "✕ 取消",
    },
}


class PageCreate(ctk.CTkFrame):
    """Встроенная страница прогресса создания (шаг визарда)."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        settings: Settings,
        on_complete: Optional[Callable] = None,
    ):
        super().__init__(parent)
        self.settings = settings
        self.on_complete = on_complete  # вызывается при показе — старт pipeline
        self._start_time = time.time()
        # Скрытый таймер синтеза сегментов (для ETA «Осталось»)
        self._synth_start_time: Optional[float] = None
        self._last_remaining_txt: str = ""
        self._paused = False
        self._finished = False
        self._pause_callback: Optional[Callable] = None
        self._resume_callback: Optional[Callable] = None
        self._cancel_callback: Optional[Callable] = None
        self._nav_restore_callback: Optional[Callable] = None

        self._create_widgets()
        # Автозапуск после отрисовки
        self.after(50, self._auto_start)

    def _t(self) -> dict:
        return CREATE_TEXTS.get(self.settings.ui_lang, CREATE_TEXTS["ru"])

    def _create_widgets(self):
        t = self._t()
        main = ctk.CTkFrame(self)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        self.title_label = ctk.CTkLabel(
            main, text=t["title"], font=ctk.CTkFont(size=18, weight="bold"),
        )
        self.title_label.pack(pady=(0, 10))

        self.stage_label = ctk.CTkLabel(
            main,
            text=STAGE_LABELS[STAGE_PREPARE],
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self.stage_label.pack(pady=(0, 6))

        self.scope_label = ctk.CTkLabel(
            main, text="", font=ctk.CTkFont(size=12), text_color="gray", wraplength=520,
        )
        self.scope_label.pack(pady=(0, 8))

        self.status_label = ctk.CTkLabel(
            main, text="Подготовка…", font=ctk.CTkFont(size=12), wraplength=520,
        )
        self.status_label.pack(pady=(0, 10))

        self.progress_bar = ctk.CTkProgressBar(main, width=440)
        self.progress_bar.pack(pady=(0, 8))
        self.progress_bar.set(0.0)

        self.time_label = ctk.CTkLabel(
            main, text="", font=ctk.CTkFont(size=12), text_color="gray",
        )
        self.time_label.pack(pady=(0, 10))

        self.detail_frame = ctk.CTkFrame(main)
        self.text_preview_label = ctk.CTkLabel(
            self.detail_frame, text="", font=ctk.CTkFont(size=11),
            wraplength=500, justify="left", anchor="w", text_color="gray",
        )
        self.text_preview_label.pack(fill="x", padx=10, pady=(5, 2))
        self.voice_engine_label = ctk.CTkLabel(
            self.detail_frame, text="", font=ctk.CTkFont(size=11),
            anchor="w", text_color="gray",
        )
        self.voice_engine_label.pack(fill="x", padx=10, pady=(0, 5))

        # Пауза / Отмена живут в нижней панели визарда
        self.pause_btn = None
        self.cancel_btn = None

    def _auto_start(self):
        if self.on_complete and not self._finished:
            self.on_complete()

    def set_pause_callback(self, cb: Callable):
        self._pause_callback = cb

    def set_resume_callback(self, cb: Callable):
        self._resume_callback = cb

    def set_cancel_callback(self, cb: Callable):
        self._cancel_callback = cb

    def set_nav_restore_callback(self, cb: Callable):
        """Включить стандартную навигацию «Назад» после завершения/отмены."""
        self._nav_restore_callback = cb

    def bind_nav_controls(self, pause_btn, cancel_btn):
        """Привязать кнопки нижней панели визарда."""
        self.pause_btn = pause_btn
        self.cancel_btn = cancel_btn
        pause_btn.configure(command=self._on_pause)
        cancel_btn.configure(command=self._on_cancel)

    def update_progress(
        self,
        status: str,
        progress: float,
        current_text: Optional[str] = None,
        voice: Optional[str] = None,
        engine: Optional[str] = None,
        segment_index: Optional[int] = None,
        segment_total: Optional[int] = None,
        stage: Optional[str] = None,
        scope_line: Optional[str] = None,
    ):
        self.after(
            0, self._do_update_progress, status, progress,
            current_text, voice, engine, segment_index, segment_total,
            stage, scope_line,
        )

    def _do_update_progress(
        self,
        status: str,
        progress: float,
        current_text: Optional[str] = None,
        voice: Optional[str] = None,
        engine: Optional[str] = None,
        segment_index: Optional[int] = None,
        segment_total: Optional[int] = None,
        stage: Optional[str] = None,
        scope_line: Optional[str] = None,
    ):
        try:
            if stage:
                self.stage_label.configure(text=STAGE_LABELS.get(stage, stage))
            if scope_line is not None:
                self.scope_label.configure(text=scope_line)
            self.status_label.configure(text=status)
            self.progress_bar.set(max(0.0, min(1.0, progress)))

            # Старт скрытого таймера — с начала синтеза сегментов
            if stage == STAGE_SYNTH and self._synth_start_time is None:
                self._synth_start_time = time.time()

            elapsed = time.time() - self._start_time
            remaining_txt = ""
            # ETA: после каждого завершённого сегмента
            # (elapsed_synth / done) * remaining
            # Обновляем только по post-complete апдейтам (без current_text),
            # где segment_index = число завершённых сегментов.
            if (
                self._synth_start_time is not None
                and stage == STAGE_SYNTH
                and current_text is None
                and segment_index is not None
                and segment_total is not None
                and segment_index > 0
            ):
                synth_elapsed = time.time() - self._synth_start_time
                left = max(0, segment_total - segment_index)
                if left == 0:
                    remaining_txt = f" | Осталось: {self._fmt(0)}"
                else:
                    remaining = (synth_elapsed / segment_index) * left
                    remaining_txt = f" | Осталось: {self._fmt(remaining)}"
            elif self._last_remaining_txt and stage == STAGE_SYNTH:
                # Пока идёт текущий сегмент — показываем последнюю оценку
                remaining_txt = self._last_remaining_txt

            if remaining_txt:
                self._last_remaining_txt = remaining_txt
            elif stage and stage != STAGE_SYNTH:
                self._last_remaining_txt = ""

            self.time_label.configure(text=f"Прошло: {self._fmt(elapsed)}{remaining_txt}")

            if current_text is not None:
                self.detail_frame.pack(fill="x", padx=10, pady=(0, 10))
                preview = current_text[:120]
                self.text_preview_label.configure(
                    text=f"📖 {preview}{'…' if len(current_text) > 120 else ''}"
                )
                eng_map = {
                    "edge": "Edge TTS", "piper": "Piper",
                    "silero": "Silero", "supertonic": "Supertonic",
                }
                parts = []
                if engine:
                    parts.append(f"⚙ {eng_map.get(engine, engine)}")
                if voice:
                    short = voice.split("-", 1)[-1] if "-" in voice else voice
                    parts.append(f"🗣 {short}")
                if segment_index is not None and segment_total is not None:
                    parts.append(f"#{segment_index}/{segment_total}")
                self.voice_engine_label.configure(text=" | ".join(parts))
            else:
                self.detail_frame.pack_forget()
        except (AttributeError, tkinter.TclError):
            pass

    def show_finished(self, ok: bool = True):
        """После завершения/отмены: убрать Pause/Cancel, вернуть «Назад» визарда."""
        self._finished = True
        if self._nav_restore_callback:
            self._nav_restore_callback()

    def set_canceling(self):
        """После нажатия «Отмена»: кнопка неактивна, ждём конец главы и склейку."""
        if self.cancel_btn is not None:
            self.cancel_btn.configure(state="disabled")
        # Статус подскажет, что процесс ещё завершает текущую главу
        try:
            self.status_label.configure(text="Отмена после текущей главы…")
        except (AttributeError, tkinter.TclError):
            pass

    def _on_pause(self):
        t = self._t()
        if self._paused:
            self._paused = False
            if self.pause_btn is not None:
                self.pause_btn.configure(text=t["pause"])
            if self._resume_callback:
                self._resume_callback()
        else:
            self._paused = True
            if self.pause_btn is not None:
                self.pause_btn.configure(text=t["resume"])
            if self._pause_callback:
                self._pause_callback()

    def _on_cancel(self):
        if self._cancel_callback:
            self._cancel_callback()

    def get_data(self) -> dict:
        return {}

    def validate(self) -> bool:
        return True

    @staticmethod
    def _fmt(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"
