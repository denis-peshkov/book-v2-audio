# Book v2 Audio

**FB2 → audiobook with AI-powered Porfiry commentary.**
![alt text](info_en.png)

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**🌍 Languages:** [Русский](README.ru.md) | [日本語](README.ja.md) | [中文](README.zh.md)

**Multi-language UI:** Russian · English · Japanese · Chinese

---

## What is this?

A desktop app (Windows/Linux) that:

1. Reads an FB2 e-book
2. Splits it into sentences
3. Adds AI-generated literary commentary between sentences
4. Converts everything to speech via **TTS** (Edge TTS cloud, Piper local, or Supertonic 3 local)
5. Saves as a single MP3 audiobook

Built with Python + CustomTkinter. Supports DeepSeek, ChatGPT, Grok, Qwen.

The interface is available in **4 languages** — switch instantly on the first wizard page.

---

## Quick Start

### Prerequisites

- Python 3.11+
- [ffmpeg](https://ffmpeg.org/) (for audio processing)
  - Linux: `sudo apt install ffmpeg`
  - Windows: download from ffmpeg.org and add to PATH
- (Optional) [piper-tts](https://github.com/rhasspy/piper) — for local CPU-based TTS (no internet needed)
- (Optional) `pip install supertonic` — for Supertonic 3 (local, high quality, ~305 MB)

### Install & Run

```bash
# 1. Create virtual environment (required on Debian 13+)
python3 -m venv venv

# 2. Activate it
source venv/bin/activate   # Linux
# venv\Scripts\activate    # Windows

# 3. Install the app and all dependencies
pip install -e .

# 4. (Optional) Install spaCy models for better sentence splitting
python -m spacy download ru_core_news_sm  # Russian
python -m spacy download en_core_web_sm   # English
python -m spacy download ja_core_news_sm  # Japanese
python -m spacy download zh_core_web_sm   # Chinese

# 5. Run
python main.py
```

Or use the Makefile:

```bash
make install   # steps 1-3
make run       # step 5
```

---

## Build a Standalone Executable

Bundle everything into a single file (no Python needed to run it):

```bash
# Activate venv first, then:
pip install pyinstaller

# Option A: use the spec file (recommended — includes logo.png)
pyinstaller AudiobookGenerator.spec

# Option B: use Makefile
make build

# The executable will be in ./dist/AudiobookGenerator
```

---

## How to Use

The app has a **7-step wizard** with multi-language support:

| Step | What you do |
|------|-------------|
| 1 | Select **UI language** (changes instantly across all pages) and **book language** (auto-selects matching TTS voices) |
| 2 | Choose AI provider (DeepSeek/ChatGPT/Grok/Qwen) and enter API key |
| 3 | Logo screen |
| 4 | Pick an FB2 file (shows title, author, chapters) |
| 5 | Choose what to narrate: all chapters, a range, or one chapter |
| 6 | Set comment frequency (every N sentences), pick a commenter role, write your own prompt, **and choose TTS engine** (Edge TTS cloud, Piper local, or Supertonic 3 local) |
| 7 | Review settings and click **Launch** |

During generation, a **detailed progress window** shows:
- Current stage (parsing, comments, synthesis, assembly)
- During synthesis: **the exact text being spoken**, voice name, engine name, and segment counter
- Elapsed and estimated remaining time
- **Pause** and **Cancel** buttons

Output: `~/audiobooks/<book_title>.mp3`

---

## TTS Engines

### Edge TTS (default, cloud-based)

Uses **free** Microsoft Edge TTS voices. High quality, but requires internet. Default voices per language:

| Language | Main Voice (Text) | Commentator Voice |
|----------|-------------------|-------------------|
| 🇷🇺 Russian | **Svetlana** (female) | **Dmitry** (male) |
| 🇬🇧 English | **Jenny** (female) | **Guy** (male) |
| 🇯🇵 Japanese | **Nanami** (female) | **Keita** (male) |
| 🇨🇳 Chinese | **Xiaoxiao** (female) | **Yunxi** (male) |

**Voices auto-update** when you change the book language on step 1. You can also override them in `~/.audiobook-generator/settings.toml`. Any voice from [the full Edge TTS list](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts) can be used.

### Piper (local, CPU)

[Piper](https://github.com/rhasspy/piper) is a fast, local neural TTS engine that runs entirely on CPU — no internet connection needed.

- **No internet required** after initial model download
- Voices are downloaded automatically on first use and cached locally
- Slightly lower quality than Edge TTS, but completely stable
- Available voices:

| Language | Voices |
|----------|--------|
| 🇷🇺 Russian | **irina** (female), **denis** (male), **dmitri** (male), **ruslan** (male) |
| 🇬🇧 English | **less** (female), **amy** (female), **joe** (male), **sam** (male), **ryan** (male), **norman** (male), **kristin** (female), **kusal** (male) |
| 🇨🇳 Chinese | **chaowen** (female), **huayan** (female), **xiao_ya** (female) |

**Installation:** Download `piper` from [releases](https://github.com/rhasspy/piper/releases) and add it to PATH, or install via `pip install piper-tts` (may require manual build on Linux).

### Supertonic 3 (local, GPU/CPU)

[Supertonic 3](https://github.com/supertone-inc/supertonic) by Supertone Inc. — modern local TTS on ONNX Runtime. Runs on CPU, no GPU needed.

- **No internet required** after initial model download (~305 MB)
- Modern architecture (flow-matching, ConvNeXt) — crisp, natural speech
- 31 languages including Russian and English
- 5-6× faster than real-time even on CPU
- 10 voices available: 5 female (F1-F5) + 5 male (M1-M5)

| Language | Main Voice (Text) | Commentator Voice |
|----------|-------------------|-------------------|
| 🇷🇺 Russian | **F1 — Anna** (female) | **M1 — Porfiry** (male) |
| 🇬🇧 English | **F1** (female) | **M1** (male) |

**Installation:** `pip install supertonic` — the model downloads automatically on first run.

---

## Built-in Commenter Roles

| Role | Style |
|------|-------|
| **Порфирий Петрович** | AI detective from Pelevin's *iPhuck 10* — literary, old-fashioned, references to Russian classics |
| **Strict Critic** | Points out weaknesses and stylistic flaws |
| **Enthusiastic Fan** | Emotional admiration for every passage |
| **Scientific Expert** | Explains historical, scientific, and cultural context |

You can also enter a **custom prompt** for your own role.

---

## Supported AI Providers

| Provider | API Key | Base URL |
|----------|---------|----------|
| DeepSeek | Required | `https://api.deepseek.com` |
| ChatGPT (OpenAI) | Required | `https://api.openai.com/v1` |
| Grok (xAI) | Required | `https://api.x.ai/v1` |
| Qwen (Alibaba Cloud) | Required | `https://dashscope.aliyuncs.com/compatible-mode/v1` |

---

## Project Structure

```
├── main.py                    # Entry point — run this
├── Makefile                   # install / run / build / clean
├── pyproject.toml             # Dependencies
├── AudiobookGenerator.spec    # PyInstaller spec (build configuration)
├── logo.png                   # Application logo
├── resources/
│   └── prompts.toml           # Commenter prompt templates
├── src/
│   ├── config/                # Settings, API key storage
│   ├── core/                  # FB2 parser, sentence splitter, AI comments,
│   │                          # TTS (abstract base + Edge + Piper + Supertonic 3), audio assembly,
│   │                          # checkpoints, pipeline orchestrator
│   ├── ui/                    # CustomTkinter GUI (7 wizard pages, progress window, components)
│   └── utils/                 # Logging, exceptions
└── tests/
```

---

## Configuration

Settings are saved to `~/.audiobook-generator/settings.toml` after first run.

You can edit: UI language, book language, AI provider, TTS engine (edge/piper/supertonic), TTS voices/speed, pause durations, comment frequency, output directory.

API keys are stored securely in your system keyring (with encrypted file fallback).

---

## Troubleshooting

**`pip install -e .` fails with `externally-managed-environment`**
→ You need a virtual environment. Run `python3 -m venv venv && source venv/bin/activate && pip install -e .`

**No sound / ffmpeg errors**
→ Install ffmpeg: `sudo apt install ffmpeg` (Linux) or download from ffmpeg.org (Windows)

**Edge TTS fails with 503 / DNS errors**
→ Try switching to **Piper** (local engine) on step 6. It doesn't need internet.

**Piper not found**
→ Install the `piper` binary and add it to PATH, or use Edge TTS instead.

**Supertonic 3 not working / pip install supertonic fails**
→ Check your Python version (3.11+). In rare cases, `pip install --upgrade pip` may be needed before installing supertonic.

---

## License

MIT
