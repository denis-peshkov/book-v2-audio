# План: Piper TTS + улучшенное окно прогресса

## 1. Что нужно сделать — обзор

Два независимых изменения:

**A. Piper TTS как второй движок** — пользователь сможет выбирать между облачным Edge TTS и локальным Piper TTS

**B. Улучшенное окно прогресса** — показывать не только %, а какой именно текст сейчас синтезируется, каким голосом, на каком движке

---

## 2. Архитектура

### Текущая структура (как сейчас)

```
TTSManager (src/core/tts_manager.py)
  └── синтезирует через edge_tts.Communicate()
```

### Новая структура

```
TTSBackend (src/core/tts_base.py) — абстрактный класс/протокол
  ├── EdgeTTSManager (src/core/tts_edge.py) — текущий код, выделенный из tts_manager.py
  └── PiperTTSManager (src/core/tts_piper.py) — новый, через piper-tts

TTSManager (src/core/tts_manager.py) — фабрика/диспетчер
  └── создаёт нужный бэкенд по config.backend
  └── все внешние вызовы (synthesize_segment, synthesize_chapter) идут через неё

ProgressCallback — расширить сигнатуру для передачи текста сегмента
```

---

## 3. Пошаговый план

### Шаг 1: Создать интерфейс `TTSBackend` (`src/core/tts_base.py`)

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any

class TTSBackend(ABC):
    """Интерфейс движка синтеза речи."""

    @abstractmethod
    async def synthesize_segment(
        self,
        text: str,
        voice: str,
        speed: float,
        output_dir: Path,
    ) -> Path:
        """Синтезировать один сегмент текста."""
        ...

    @abstractmethod
    async def get_available_voices(self, lang: str) -> List[Dict[str, Any]]:
        """Получить список доступных голосов для языка."""
        ...

    @abstractmethod
    async def close(self):
        """Освободить ресурсы."""
        ...
```

### Шаг 2: Переименовать `TTSManager` → `EdgeTTSManager` (`src/core/tts_edge.py`)

- Весь существующий код `TTSManager` (synthesize_segment, synthesize_chapter, get_available_voices) переезжает в `EdgeTTSManager`
- `EdgeTTSManager(config)` implements `TTSBackend`

### Шаг 3: Создать `PiperTTSManager` (`src/core/tts_piper.py`)

Использует библиотеку `piper-tts`:

```python
class PiperTTSManager(TTSBackend):
    def __init__(self, config: TTSConfig):
        self.config = config
        self._voice_cache_dir = Path.home() / ".audiobook-generator" / "piper-voices"
        self._voice_cache_dir.mkdir(parents=True, exist_ok=True)
        # Piper работает через subprocess/pipe, т.к. запускает ONNX модель
        # Используем piper-tts Python binding

    async def synthesize_segment(self, text, voice, speed, output_dir) -> Path:
        # 1. Загрузить модель если ещё нет (с HuggingFace)
        # 2. Конвертировать voice name в Piper-формат
        # 3. Запустить синтез
        # 4. Сохранить как .mp3
        ...

    async def get_available_voices(self, lang: str) -> List[dict]:
        # Вернуть список голосов для языка
        # Для русского: irina (женский), denis (мужской) — medium quality
        ...
```

**Подробнее про Piper:**

- Библиотека: `piper-tts` (PyPI)
- Модели скачиваются с HuggingFace: https://huggingface.co/rhasspy/piper-voices/tree/main/ru/ru_RU
- Доступные русские голоса:
  - `ru_RU-irina-medium` — женский, ~50MB
  - `ru_RU-denis-medium` — мужской, ~50MB
- Формат вывода: WAV (конвертировать в MP3 через pydub/ffmpeg)
- Скорость: синтез быстрее реального времени на CPU (типично 3-5 секунд на 1 минуту речи)
- Не зависит от интернета — идеально для офлайн

**Важно:** Piper не поддерживает SSML и изменение скорости (rate) на уровне движка. Скорость можно менять пост-обработкой через ffmpeg (аудио strech). Реализуем через `pydub` или `subprocess ffmpeg atempo`.

### Шаг 4: Обновить `TTSConfig` (`src/core/tts_manager.py`)

```python
@dataclass
class TTSConfig:
    backend: str = "edge"  # "edge" | "piper"
    main_voice: str = "ru-RU-SvetlanaNeural"
    comment_voice: str = "ru-RU-DmitryNeural"
    main_speed: float = 1.0
    comment_speed: float = 1.0
    pause_before_comment: float = 1.0
    pause_after_comment: float = 0.7
    pause_between_sentences: float = 0.3
```

### Шаг 5: Превратить `TTSManager` в фабрику/диспетчер

```python
class TTSManager:
    def __init__(self, config: TTSConfig):
        self.config = config
        if config.backend == "edge":
            self._backend = EdgeTTSManager(config)
        elif config.backend == "piper":
            self._backend = PiperTTSManager(config)
        else:
            raise ValueError(f"Unknown TTS backend: {config.backend}")

    async def synthesize_segment(self, text, voice, speed, output_dir) -> Path:
        return await self._backend.synthesize_segment(text, voice, speed, output_dir)

    async def synthesize_chapter(self, text_segments, comment_segments, chapter_dir, progress_callback) -> Path:
        return await self._backend.synthesize_chapter(
            text_segments, comment_segments, chapter_dir, progress_callback
        )

    async def get_available_voices(self, lang: str) -> List[dict]:
        return await self._backend.get_available_voices(lang)

    async def close(self):
        if hasattr(self._backend, 'close'):
            await self._backend.close()
```

### Шаг 6: Улучшить прогресс-колбэк

Сейчас сигнатура: `progress_callback: Callable[[int, int], None]` (completed, total)

Нужно расширить до: `Callable[[int, int, str], None]` (completed, total, current_text)

**В `synthesize_chapter`** — передавать текущий текст сегмента:

```python
if progress_callback:
    progress_callback(completed, total, text[:100])  # Первые 100 символов
```

**В `EdgeTTSManager.synthesize_chapter`** — добавить параметр `current_text` и вызывать колбэк с ним.

### Шаг 7: Улучшить `ProgressWindow` (`src/ui/progress_window.py`)

Добавить новые виджеты:

1. **Поле "Текущий сегмент"** — `ctk.CTkTextbox` (readonly, 3-4 строки высотой), показывает текст который сейчас синтезируется
2. **Метка "Голос/Движок"** — показывает какой голос и какой бэкенд
3. **Счётчик сегментов** — "Сегмент 42/240"

Примерно так:

```
┌──────────────────────────────────┐
│         Создание аудиокниги        │
│                                    │
│  Глава 4/8: синтез речи...         │
│                                    │
│  ████████████████░░░░░░░ 60%       │
│  Прошло: 25:00 | Осталось: 15:30   │
│                                    │
│  ┌──────────────────────────────┐  │
│  │ Текст: "В комнату вошёл      │  │
│  │ высокий человек в чёрном...  │  │
│  └──────────────────────────────┘  │
│                                    │
│  Движок: Piper | Голос: Ирина     │
│  Сегмент: 142/240                  │
│                                    │
│  [⏸ Пауза]            [✕ Отмена]  │
└──────────────────────────────────┘
```

Сигнатура `update_progress` расширяется:

```python
def update_progress(
    self,
    status: str,
    progress: float,
    current_text: Optional[str] = None,
    voice: Optional[str] = None,
    engine: Optional[str] = None,
    segment_index: Optional[int] = None,
    segment_total: Optional[int] = None,
):
    self.after(0, self._do_update_progress, status, progress,
               current_text, voice, engine, segment_index, segment_total)
```

### Шаг 8: Обновить `Settings` и `defaults.toml`

**`src/config/settings.py`:**
```python
@dataclass
class Settings:
    # ... existing fields
    tts_backend: str = "edge"  # "edge" | "piper"
```

**`src/config/defaults.toml`:**
```toml
tts_backend = "edge"
```

### Шаг 9: UI — добавить выбор TTS бэкенда

Добавить в существующий wizard (лучшее место — шаг 6, PageComments, или шаг 5, PageScope):

**Вариант: добавить секцию в PageScope** (шаг 5), где пользователь выбирает:
- Тип: "Облачный Edge TTS" или "Локальный Piper TTS"
- После выбора меняются доступные голоса на странице запуска

Или проще: добавить выпадающий список в **PageLaunch** (шаг 7) как дополнительную опцию перед запуском.

**Рекомендуемый вариант:** Добавить выпадающий список в **PageComments** (шаг 6) под настройками комментариев.

Псевдокод:
```python
# Секция выбора TTS
tts_frame = ctk.CTkFrame(self)
tts_frame.pack(fill="x", padx=40, pady=10)

self.tts_backend_var = ctk.StringVar(value=self.settings.tts_backend)
tts_option = ctk.CTkOptionMenu(
    tts_frame,
    values=["edge", "piper"],
    variable=self.tts_backend_var,
    command=self._on_tts_backend_change,
)
```

### Шаг 10: Обновить `app.py` — передавать `tts_backend` в `TTSConfig`

```python
tts_config = TTSConfig(
    backend=self.settings.tts_backend,
    main_voice=self.settings.main_voice,
    comment_voice=self.settings.comment_voice,
    main_speed=self.settings.main_speed,
    comment_speed=self.settings.comment_speed,
    ...
)
```

### Шаг 11: Piper голоса — маппинг

Создать маппинг Piper-голосов для каждого языка:

```python
PIPER_VOICES = {
    "ru": {"main": "ru_RU-irina-medium", "comment": "ru_RU-denis-medium"},
    "en": {"main": "en_US-less-medium", "comment": "en_US-amy-medium"},
    "ja": {"main": "ja_JP-taka-medium", "comment": "ja_JP-taka-medium"},  # только один японский голос
    "zh": {"main": "zh_CN-xiaobei-medium", "comment": "zh_CN-xiaobei-medium"},
}
```

При первом запуске Piper-модели скачиваются с HuggingFace в `~/.audiobook-generator/piper-voices/`.

---

## 4. Обработка ошибок

- Если Piper-модель не скачалась (нет интернета) — показать ошибку, предложить переключиться на Edge TTS
- Если piper-tts не установлен (`ImportError`) — показать понятное сообщение (`pip install piper-tts`)
- Piper не поддерживает изменение скорости напрямую — использовать ffmpeg atempo для изменения темпа

---

## 5. Файлы для изменения/создания

| Файл | Действие |
|------|----------|
| `src/core/tts_base.py` | **Создать** — интерфейс TTSBackend |
| `src/core/tts_edge.py` | **Создать** — EdgeTTSManager (код из tts_manager.py) |
| `src/core/tts_piper.py` | **Создать** — PiperTTSManager |
| `src/core/tts_manager.py` | **Переписать** — фабрика/диспетчер |
| `src/core/pipeline.py` | **Изменить** — передавать текст в прогресс-колбэк |
| `src/ui/progress_window.py` | **Изменить** — добавить отображение текста, голоса, движка |
| `src/ui/app.py` | **Изменить** — передавать tts_backend в конфиг |
| `src/config/settings.py` | **Изменить** — добавить tts_backend |
| `src/config/defaults.toml` | **Изменить** — добавить tts_backend |
| `src/ui/pages/page_comments.py` | **Изменить** — добавить выбор TTS бэкенда |
| `src/ui/pages/page_launch.py` | **Изменить** — показать выбранный TTS бэкенд |
| `pyproject.toml` | **Изменить** — добавить piper-tts как опциональную зависимость |

---

## 6. Зависимости

```toml
[project.optional-dependencies]
tts = ["piper-tts"]
```

Piper не должен быть обязательной зависимостью — если пользователь не хочет его ставить, Edge TTS работает как раньше.
