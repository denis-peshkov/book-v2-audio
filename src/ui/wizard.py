"""
Контроллер пошагового мастера настройки.
Управляет переключением между страницами и сбором данных.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Callable, List, Optional, Type

import customtkinter as ctk

from src.config.settings import Settings
from src.ui.pages import (
    PageLanguage,
    PageAPI,
    PageLogo,
    PageFile,
    PageScope,
    PageComments,
    PageLaunch,
    PageCreate,
)

logger = logging.getLogger(__name__)

# Названия шагов на разных языках
STEP_NAMES = {
    "ru": ["Язык", "API", "О нас", "Файл", "Комментарии", "Объём", "Запуск", "Создание"],
    "en": ["Language", "API", "About", "File", "Comments", "Scope", "Launch", "Create"],
    "ja": ["言語", "API", "概要", "ファイル", "コメント", "範囲", "開始", "作成"],
    "zh": ["语言", "API", "关于", "文件", "评论", "范围", "启动", "创建"],
}

# Тексты навигационных кнопок
NAV_TEXTS = {
    "ru": {"back": "← Назад", "next": "Далее →"},
    "en": {"back": "← Back", "next": "Next →"},
    "ja": {"back": "← 戻る", "next": "次へ →"},
    "zh": {"back": "← 返回", "next": "下一步 →"},
}


class WizardController:
    """Контроллер пошагового мастера.

    Управляет последовательностью страниц, навигацией и сбором данных.
    """

    def __init__(
        self,
        parent: ctk.CTkFrame,
        settings: Settings,
        on_complete: Optional[Callable] = None,
        on_lang_change: Optional[Callable[[str], None]] = None,
    ):
        self.parent = parent
        self.settings = settings
        self.on_complete = on_complete
        self.on_lang_change = on_lang_change
        self.current_page_index = 0
        self.pages: List[ctk.CTkFrame] = []

        # Индикатор шагов
        self.steps_frame = ctk.CTkFrame(parent, height=40)
        self.steps_frame.pack(fill="x", padx=5, pady=(5, 0))
        self.steps_frame.pack_propagate(False)

        self.step_labels: List[ctk.CTkLabel] = []
        self._create_step_indicator()

        # Контейнер для содержимого страницы (с прокруткой, если не помещается)
        self.content_frame = ctk.CTkScrollableFrame(parent)
        self.content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._enable_mousewheel()

        # Навигационные кнопки
        self.nav_frame = ctk.CTkFrame(parent, height=50)
        self.nav_frame.pack(fill="x", padx=5, pady=(0, 5))
        self.nav_frame.pack_propagate(False)

        nav_t = NAV_TEXTS.get(self.settings.ui_lang, NAV_TEXTS["ru"])
        self.back_btn = ctk.CTkButton(
            self.nav_frame,
            text=nav_t["back"],
            command=self.go_back,
            state="disabled",
            width=100,
        )
        self.back_btn.pack(side="left", padx=10, pady=5)

        self.next_btn = ctk.CTkButton(
            self.nav_frame,
            text=nav_t["next"],
            command=self.go_next,
            width=100,
        )
        self.next_btn.pack(side="right", padx=10, pady=5)

        # Пауза / Отмена — на шаге «Создание» вместо «Далее»
        create_t = self._create_nav_texts()
        self.pause_btn = ctk.CTkButton(
            self.nav_frame,
            text=create_t["pause"],
            width=130,
        )
        self.cancel_btn = ctk.CTkButton(
            self.nav_frame,
            text=create_t["cancel"],
            width=130,
            fg_color="red",
            hover_color="darkred",
        )

    def _create_step_indicator(self):
        """Создание индикатора шагов вверху мастера."""
        lang = self.settings.ui_lang
        step_names = STEP_NAMES.get(lang, STEP_NAMES["ru"])
        for i, name in enumerate(step_names):
            label = ctk.CTkLabel(
                self.steps_frame,
                text=f"{i + 1}. {name}",
                font=ctk.CTkFont(size=10),
            )
            label.pack(side="left", padx=8, pady=5, expand=True)
            self.step_labels.append(label)

    def update_step_language(self, lang_code: str):
        """Обновление языка шагов и навигационных кнопок."""
        step_names = STEP_NAMES.get(lang_code, STEP_NAMES["ru"])
        for i, label in enumerate(self.step_labels):
            if i < len(step_names):
                label.configure(text=f"{i + 1}. {step_names[i]}")

        # Обновляем навигационные кнопки
        nav_t = NAV_TEXTS.get(lang_code, NAV_TEXTS["ru"])
        self.back_btn.configure(text=nav_t["back"])
        # Обновляем кнопку "Далее" только если она видна (не на последней странице)
        try:
            if self.next_btn.winfo_viewable():
                self.next_btn.configure(text=nav_t["next"])
        except Exception:
            pass
        create_t = self._create_nav_texts(lang_code)
        try:
            if self.pause_btn.winfo_viewable():
                # Не затираем «Продолжить», если сейчас на паузе
                page = self.get_current_page()
                if not (hasattr(page, "_paused") and page._paused):
                    self.pause_btn.configure(text=create_t["pause"])
            if self.cancel_btn.winfo_viewable():
                self.cancel_btn.configure(text=create_t["cancel"])
        except Exception:
            pass

    def show_first_page(self):
        """Показать первую страницу."""
        self._show_page(0)

    def _show_page(self, index: int):
        """Показать страницу с указанным индексом."""
        # Очищаем контейнер
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Создаём страницу
        page_classes = [
            PageLanguage,
            PageAPI,
            PageLogo,
            PageFile,
            PageComments,
            PageScope,
            PageLaunch,
            PageCreate,
        ]

        if index < 0 or index >= len(page_classes):
            return

        page_class = page_classes[index]
        is_create = index == len(page_classes) - 1
        is_launch = index == len(page_classes) - 2

        # Launch → переход на Создание; Создание → старт pipeline (on_complete)
        if is_create:
            page_callback = self.on_complete
        elif is_launch:
            page_callback = self._on_launch_clicked
        else:
            page_callback = self._on_page_complete

        # Для страницы языка передаём дополнительный колбэк смены языка
        kwargs = {}
        if index == 0 and self.on_lang_change:
            kwargs["on_lang_change"] = self.on_lang_change

        page = page_class(
            self.content_frame,
            self.settings,
            page_callback,
            **kwargs,
        )
        page.pack(fill="x", expand=False)
        self._current_page = page

        if is_create and hasattr(page, "set_nav_restore_callback"):
            page.set_nav_restore_callback(self._restore_nav_after_create)
        if is_create and hasattr(page, "bind_nav_controls"):
            page.bind_nav_controls(self.pause_btn, self.cancel_btn)

        self.current_page_index = index

        # Обновляем индикатор шагов
        self._update_step_indicator(index)

        # Навигация: на Создании — Пауза/Отмена вместо Далее; Назад выключен
        if is_create:
            self.next_btn.pack_forget()
            self.back_btn.configure(state="disabled")
            create_t = self._create_nav_texts()
            self.pause_btn.configure(text=create_t["pause"], state="normal")
            self.cancel_btn.configure(text=create_t["cancel"], state="normal")
            # side=right: первым пакуется правее
            self.cancel_btn.pack(side="right", padx=10, pady=5)
            self.pause_btn.pack(side="right", padx=10, pady=5)
        else:
            self.pause_btn.pack_forget()
            self.cancel_btn.pack_forget()
            self.back_btn.configure(state="normal" if index > 0 else "disabled")
            self.next_btn.pack(side="right", padx=10, pady=5)
            nav_t = NAV_TEXTS.get(self.settings.ui_lang, NAV_TEXTS["ru"])
            self.next_btn.configure(
                text=nav_t["next"],
                fg_color=["#3B8ED0", "#1F6AA5"],
                hover_color=["#36719F", "#144870"],
            )

        # После длинной предыдущей страницы скролл мог остаться внизу —
        # поднимаем к заголовку нового шага.
        self._scroll_content_to_top()

    def _enable_mousewheel(self):
        """Прокрутка колесом мыши и тачпадом над областью шага.

        Tk 9 (aqua/win32): двухпальцевый жест тачпада даёт <TouchpadScroll>,
        а не <MouseWheel> (TIP 684). CTk это ещё не обрабатывает.
        """
        frame = self.content_frame
        canvas = frame._parent_canvas
        parent = frame._parent_frame
        root = parent.winfo_toplevel()

        try:
            frame.master = canvas
        except Exception:
            pass

        # Штатный CTk-фильтр часто ломается на дочерних CTk-виджетах
        frame._check_if_valid_scroll = lambda _widget: False

        def _pointer_over_content() -> bool:
            try:
                x, y = parent.winfo_pointerxy()
                x0, y0 = parent.winfo_rootx(), parent.winfo_rooty()
                return (
                    x0 <= x < x0 + max(parent.winfo_width(), 1)
                    and y0 <= y < y0 + max(parent.winfo_height(), 1)
                )
            except Exception:
                return False

        def _event_in_content(event) -> bool:
            if _pointer_over_content():
                return True
            widget = getattr(event, "widget", None)
            if widget is None:
                return False
            try:
                path = str(widget)
                return (
                    str(canvas) in path
                    or str(frame) in path
                    or str(parent) in path
                )
            except Exception:
                return False

        def _over_textbox(widget) -> bool:
            w = widget
            for _ in range(32):
                if w is None:
                    return False
                try:
                    if isinstance(w, ctk.CTkTextbox):
                        return True
                    if w.winfo_class() == "Text":
                        return True
                    parent_path = w.winfo_parent()
                    w = w.nametowidget(parent_path) if parent_path else None
                except Exception:
                    return False
            return False

        def _refresh_scrollregion():
            try:
                bbox = canvas.bbox("all")
                if bbox is not None:
                    canvas.configure(scrollregion=bbox)
            except Exception:
                pass

        def _scroll_pixels(delta_x: int, delta_y: int):
            if not delta_x and not delta_y:
                return
            _refresh_scrollregion()
            try:
                canvas.tk.call("tk::ScrollByPixels", canvas._w, delta_x, delta_y)
                return
            except Exception:
                pass
            if delta_y:
                canvas.yview_scroll(int(-delta_y), "units")
            if delta_x:
                canvas.xview_scroll(int(-delta_x), "units")

        def _on_touchpad_scroll(event):
            """Tk 9+: двухпальцевый скролл тачпада."""
            if not _event_in_content(event):
                return
            if _over_textbox(getattr(event, "widget", None)):
                return
            try:
                dx, dy = canvas.tk.call(
                    "tk::PreciseScrollDeltas",
                    getattr(event, "delta", 0),
                )
                delta_x, delta_y = int(dx), int(dy)
            except Exception:
                return
            if delta_x == 0 and delta_y == 0:
                return
            _scroll_pixels(delta_x, delta_y)
            return "break"

        def _on_mousewheel(event):
            """Обычное колесо мыши (и старый Tk 8.x, где тачпад = MouseWheel)."""
            if not _event_in_content(event):
                return
            if _over_textbox(getattr(event, "widget", None)):
                return
            _refresh_scrollregion()

            delta = getattr(event, "delta", 0) or 0
            num = getattr(event, "num", None)
            try:
                delta = int(delta)
            except (TypeError, ValueError):
                delta = 0

            if sys.platform == "darwin":
                steps = -delta
            elif sys.platform.startswith("win"):
                steps = int(-delta / 120) if delta else 0
            elif num == 4:
                steps = -3
            elif num == 5:
                steps = 3
            else:
                steps = -delta if delta else 0

            if not steps:
                return
            canvas.yview_scroll(steps, "units")
            return "break"

        root.bind_all("<MouseWheel>", _on_mousewheel, add="+")
        root.bind_all("<Button-4>", _on_mousewheel, add="+")
        root.bind_all("<Button-5>", _on_mousewheel, add="+")
        # Tk 9 aqua/win32: тачпад больше не шлёт MouseWheel
        try:
            root.bind_all("<TouchpadScroll>", _on_touchpad_scroll, add="+")
        except Exception:
            pass

    def _scroll_content_to_top(self):
        """Сбросить вертикальный скролл content_frame в начало."""
        def _do_scroll():
            try:
                self.content_frame.update_idletasks()
                canvas = getattr(self.content_frame, "_parent_canvas", None)
                if canvas is not None:
                    canvas.yview_moveto(0)
            except Exception:
                pass

        _do_scroll()
        # Повтор после раскладки новой страницы (иначе scrollregion ещё старый)
        try:
            self.content_frame.after(1, _do_scroll)
            self.content_frame.after(50, _do_scroll)
        except Exception:
            pass

    def _create_nav_texts(self, lang: Optional[str] = None) -> dict:
        from src.ui.pages.page_create import CREATE_TEXTS
        code = lang or self.settings.ui_lang
        return CREATE_TEXTS.get(code, CREATE_TEXTS["ru"])

    def _on_launch_clicked(self, *args, **kwargs):
        """Совместимость: раньше зелёная кнопка на Запуске."""
        self.go_next()

    def _restore_nav_after_create(self):
        """После завершения/отмены создания — стандартная «Назад» к Запуску."""
        self.pause_btn.pack_forget()
        self.cancel_btn.pack_forget()
        self.next_btn.pack_forget()
        self.back_btn.configure(state="normal")

    def get_current_page(self):
        """Текущая страница визарда."""
        return getattr(self, "_current_page", None) or self._get_current_page()

    def _update_step_indicator(self, active_index: int):
        """Обновление подсветки активного шага."""
        for i, label in enumerate(self.step_labels):
            if i == active_index:
                label.configure(text_color="#3B8ED0")  # активный
            elif i < active_index:
                label.configure(text_color="green")  # пройденный
            else:
                label.configure(text_color="gray")  # будущий

    def _on_page_complete(self, data: dict):
        """Обработчик завершения страницы."""
        # Обновляем настройки из данных страницы
        for key, value in data.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)

    def go_back(self):
        """Переход на предыдущую страницу."""
        if self.current_page_index > 0:
            self._show_page(self.current_page_index - 1)

    def go_next(self):
        """Переход на следующую страницу."""
        # Вызываем валидацию текущей страницы
        current_page = self._get_current_page()
        if current_page and hasattr(current_page, "validate"):
            if not current_page.validate():
                return

        # Собираем данные с текущей страницы
        if current_page and hasattr(current_page, "get_data"):
            data = current_page.get_data()
            self._on_page_complete(data)

        max_index = 7  # 8 страниц (0-7)
        if self.current_page_index < max_index:
            self._show_page(self.current_page_index + 1)
        else:
            if self.on_complete:
                self.on_complete()

    def _get_current_page(self):
        """Получение ссылки на текущую страницу."""
        children = self.content_frame.winfo_children()
        return children[0] if children else None

    def set_api_key(self, key: str):
        """Установка API-ключа (вызывается при загрузке сохранённого)."""
        # Пробуем найти страницу API и установить ключ
        for page in self.pages:
            if hasattr(page, "set_api_key"):
                page.set_api_key(key)
                break
