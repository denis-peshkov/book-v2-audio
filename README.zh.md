# Book v2 Audio

**将 FB2 电子书转换为带 AI 评论的有声读物。**
![alt text](info_cn.png)

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**🌍 语言:** [English](README.md) | [Русский](README.ru.md) | [日本語](README.ja.md)

**多语言界面:** 中文 · English · Русский · 日本語

---

## 简介

桌面应用程序（Windows/Linux），可以：

1. 读取 FB2 电子书
2. 拆分为句子
3. **可选** 在句子之间添加 AI 生成的评论（可禁用）
4. 通过 **TTS**（Edge TTS、Piper、Supertonic 3 或 Silero TTS v5）合成语音
5. 保存为单个 MP3 文件

技术栈：Python + CustomTkinter。支持 DeepSeek、ChatGPT、Grok、Qwen。

界面支持 **4 种语言** — 在向导第一步即可即时切换。

---

## 快速开始

### 前提条件

- Python 3.11+
- [ffmpeg](https://ffmpeg.org/)（音频处理需要）
  - Linux: `sudo apt install ffmpeg`
  - Windows: 从 ffmpeg.org 下载并添加到 PATH
- （可选）[piper-tts](https://github.com/rhasspy/piper) — 用于本地 CPU TTS（无需网络）
- （可选）`pip install -e .[supertonic]` — Supertonic 3（本地，31种语言，~305 MB）
- （可选）`pip install -e .[silero]` — Silero TTS v5（本地，开源中俄语质量最佳，~150 MB，需要 PyTorch）

### 安装与运行

```bash
# 1. 创建虚拟环境（Debian 13+ 必须）
python3 -m venv venv

# 2. 激活
source venv/bin/activate   # Linux
# venv\Scripts\activate    # Windows

# 3. 安装应用及核心依赖
pip install -e .

# 4. （可选）安装额外 TTS 引擎
pip install -e .[supertonic]  # Supertonic 3

# 在 CPU 上使用 Silero（推荐 — 安装 PyTorch 和所有依赖）：
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install -e .[silero]

#   （以上两条命令是 Silero 必需的；不需要可跳过）

# 5. （可选）安装 spaCy 模型以提高分句精度
python -m spacy download ru_core_news_sm  # 俄语
python -m spacy download en_core_web_sm   # 英语
python -m spacy download ja_core_news_sm  # 日语
python -m spacy download zh_core_web_sm   # 中文

# 6. 运行
python main.py
```

或使用 Makefile：

```bash
make install   # 步骤 1-3
make run       # 步骤 6
```

---

## 构建独立可执行文件

打包成单个文件，无需 Python 即可运行：

```bash
# 先激活 venv，然后：
pip install pyinstaller

# 选项 A：使用 spec 文件（推荐 — 包含 logo.png）
pyinstaller AudiobookGenerator.spec

# 选项 B：使用 Makefile
make build

# 可执行文件：./dist/AudiobookGenerator
```

---

## 使用方法

**7 步向导**（多语言支持）：

| 步骤 | 操作 |
|------|------|
| 1 | 选择**界面语言**（所有页面即时切换）和**书籍语言**（自动匹配 TTS 语音） |
| 2 | 选择 AI 提供商（DeepSeek/ChatGPT/Grok/Qwen）并输入 API 密钥。**如果不需要 AI 评论，只需点击「下一步」，密钥不是必需的** |
| 3 | 徽标页面 |
| 4 | 选择 FB2 文件（显示标题、作者、章节） |
| 5 | 选择范围：所有章节、范围或单个章节 |
| 6 | 开启/关闭 **AI 评论**（复选框）。设置评论频率、评论者角色、自定义提示词，**并选择 TTS 引擎**（Edge TTS、Piper、Supertonic 3 或 Silero TTS v5） |
| 7 | 检查设置并点击**启动** |

生成过程中，**详细的进度窗口**会显示：
- 当前阶段（解析、评论、合成、组装）
- 合成期间：**正在朗读的文本**、语音名称、引擎名称和片段计数器
- 已用时间和预计剩余时间
- **暂停**和**取消**按钮

输出位置：`~/audiobooks/<书名>.mp3`

---

## TTS 引擎

### Edge TTS（默认，云端）

应用使用**免费**的 Microsoft Edge TTS 语音。高质量，但需要网络连接。每种语言的默认语音：

| 语言 | 主语音（文本） | 评论员语音 |
|------|--------------|-----------|
| 🇷🇺 俄语 | **Svetlana**（女声） | **Dmitry**（男声） |
| 🇬🇧 英语 | **Jenny**（女声） | **Guy**（男声） |
| 🇯🇵 日语 | **Nanami**（女声） | **Keita**（男声） |
| 🇨🇳 中文 | **Xiaoxiao**（女声） | **Yunxi**（男声） |

**语音会自动更新** — 在步骤 1 中更改书籍语言时，对应的默认语音会自动应用。也可以在 `~/.audiobook-generator/settings.toml` 中覆盖。可以使用[完整的 Edge TTS 语音列表](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts)中的任何语音。

### Piper（本地，CPU）

[Piper](https://github.com/rhasspy/piper) 是一个快速的本地神经 TTS 引擎，完全在 CPU 上运行 — 无需网络连接。

- **初始模型下载后无需网络**
- 语音在首次使用时自动下载并缓存到本地
- 质量略低于 Edge TTS，但完全稳定
- 可用语音：

| 语言 | 语音 |
|------|------|
| 🇷🇺 俄语 | **irina**（女声）、**denis**（男声）、**dmitri**（男声）、**ruslan**（男声） |
| 🇬🇧 英语 | **less**（女声）、**amy**（女声）、**joe**（男声）、**sam**（男声）、**ryan**（男声）、**norman**（男声）、**kristin**（女声）、**kusal**（男声） |
| 🇨🇳 中文 | **chaowen**（女声）、**huayan**（女声）、**xiao_ya**（女声） |

**安装方法：** 从[发布页面](https://github.com/rhasspy/piper/releases)下载 `piper` 并添加到 PATH，或通过 `pip install piper-tts` 安装（在 Linux 上可能需要手动编译）。

### Supertonic 3（本地，GPU/CPU）

[Supertonic 3](https://github.com/supertone-inc/supertonic) 由 Supertone Inc. 开发 — 基于 ONNX Runtime 的现代本地 TTS。在 CPU 上运行，无需 GPU。

- **初始模型下载后无需网络**（~305 MB）
- 现代架构（flow-matching, ConvNeXt）— 清晰自然的语音
- 31 种语言，包括俄语和英语
- 即使在 CPU 上也比实时快 5-6 倍
- 10 种语音：5 个女声（F1-F5）+ 5 个男声（M1-M5）

| 语言 | 主语音（文本） | 评论员语音 |
|------|--------------|-----------|
| 🇷🇺 俄语 | **F1 — Anna**（女声） | **M1 — Porfiry**（男声） |
| 🇬🇧 英语 | **F1**（女声） | **M1**（男声） |

**安装：** `pip install -e .[supertonic]` — 模型在首次运行时自动下载（~305 MB）。

### Silero TTS v5（本地，CPU）

[Silero TTS v5](https://github.com/snakers4/silero-models) — 由 Silero 团队开发的预训练 TTS 模型。开源中俄语质量最佳。

- **初始模型下载后无需网络**（~150 MB）
- 自动重音和同形词支持（俄语）
- FastSpeech 2 架构 — 出色的清晰度
- UTMOS 3.04（俄语自然度接近真人）
- 支持 SSML

| 语言 | 主语音（文本） | 评论员语音 |
|------|--------------|-----------|
| 🇷🇺 俄语 | **xenia**（女声） | **eugene**（男声） |
| 🇬🇧 英语 | **lj_16khz**（女声） | **random**（男声） |

**安装：**
```bash
# CPU（推荐给大多数用户）：
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install -e .[silero]

# 如果有 CUDA GPU：
pip install -e .[silero]
```

模型（v5_ru）在首次使用时自动下载（到 venv 的 `silero_tts/silero_models/` 目录）— 首次约需一分钟，之后可离线使用。

Silero 自动检测文本语言：**西里尔字母** → 俄语语音（xenia/eugene），**拉丁字母** → 英语语音（lj_16khz）。其他语言（日语、中文）请使用 **Edge TTS** 或 **Supertonic 3**。

---

## 🎯 完全离线模式

您可以**无需互联网**运行整个流程：

1. **步骤 2**：跳过 API 密钥（不会生成 AI 评论）
2. **步骤 6**：取消选中 **"生成 AI 评论"**
3. 选择本地 TTS 引擎：**Piper**、**Supertonic 3** 或 **Silero TTS v5**

无需 API 调用，无需云依赖。只需 FB2 解析 + 本地 TTS → 有声书。

---

## 内置评论者角色

| 角色 | 风格 |
|------|------|
| **波尔菲里·彼得罗维奇** | 佩列温《iPhuck 10》中的 AI 侦探 — 文学化、老派、引用俄罗斯经典 |
| **严厉的评论家** | 指出弱点和文体错误 |
| **热情的粉丝** | 对每个段落都赞叹不已 |
| **科学专家** | 解释历史、科学和文化背景 |

也可以输入**自定义提示词**来创建自己的角色。

---

## 支持的 AI 提供商

| 提供商 | API 密钥 | 基础 URL |
|--------|---------|----------|
| DeepSeek | 需要（用于评论） | `https://api.deepseek.com` |
| ChatGPT (OpenAI) | 需要（用于评论） | `https://api.openai.com/v1` |
| Grok (xAI) | 需要（用于评论） | `https://api.x.ai/v1` |
| Qwen (阿里云) | 需要（用于评论） | `https://dashscope.aliyuncs.com/compatible-mode/v1` |

**注意：** 仅在使用 AI 评论时需要 API 密钥。离线模式下可完全跳过此步骤。

---

## 项目结构

```
├── main.py                    # 入口点 — 运行此文件
├── Makefile                   # install / run / build / clean
├── pyproject.toml             # 依赖关系
├── AudiobookGenerator.spec    # PyInstaller spec（构建配置）
├── logo.png                   # 应用程序徽标
├── resources/
│   └── prompts.toml           # 评论者提示词模板
├── src/
│   ├── config/                # 设置、API 密钥存储
│   ├── core/                  # FB2 解析器、句子分割、AI 评论、
│   │                          # TTS（抽象基类 + Edge + Piper + Supertonic 3 + Silero）、
│   │                          # 音频组装、检查点、流程编排器
│   ├── ui/                    # CustomTkinter GUI（7 步向导、进度窗口、组件）
│   └── utils/                 # 日志、异常
└── tests/
```

---

## 配置

首次运行后，设置保存在 `~/.audiobook-generator/settings.toml` 中。

可修改：界面语言、书籍语言、AI 提供商、TTS 引擎（edge/piper/supertonic/silero）、TTS 语音/速度、停顿时间、评论频率、评论开关、输出目录。

API 密钥安全存储在系统密钥环中（附带加密文件后备方案）。

---

## 故障排除

**`pip install -e .` 失败，提示 `externally-managed-environment`**
→ 需要使用虚拟环境：`python3 -m venv venv && source venv/bin/activate && pip install -e .`

**没有声音 / ffmpeg 错误**
→ 安装 ffmpeg：`sudo apt install ffmpeg`（Linux）或从 ffmpeg.org 下载（Windows）

**Edge TTS 失败，出现 503 / DNS 错误**
→ 尝试在步骤 6 切换到本地引擎（**Piper**、**Supertonic 3** 或 **Silero**）。

**找不到 Piper**
→ 安装 `piper` 二进制文件并添加到 PATH，或使用其他引擎。

**Supertonic 3 不工作 / pip install supertonic 失败**
→ 检查 Python 版本（3.11+）。极少数情况下可能需要先运行 `pip install --upgrade pip`。

**Silero TTS v5 不工作 / torch 导入失败**
→ 确保已安装 PyTorch：`pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu`
→ 首次运行时模型会自动下载（~150 MB），可能需要一分钟。

---

## 许可证

MIT
