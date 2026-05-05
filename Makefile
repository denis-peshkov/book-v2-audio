# Makefile для Audiobook Generator
# Использует venv/bin для изоляции от системного Python (Debian 13+ PEP 668)

VENV_PYTHON = venv/bin/python
VENV_PIP = venv/bin/pip
VENV_PYINSTALLER = venv/bin/pyinstaller

.PHONY: install install-dev run build clean test lint

# Создание виртуального окружения
venv:
	python3 -m venv venv
	$(VENV_PIP) install --upgrade pip setuptools wheel

# Установка зависимостей
install: venv
	$(VENV_PIP) install -e .

install-dev: venv
	$(VENV_PIP) install -e ".[dev]"

# Запуск приложения
run:
	$(VENV_PYTHON) main.py

# Сборка в единый исполняемый файл (из venv)
build:
	$(VENV_PYINSTALLER) --onefile --windowed \
		--name "AudiobookGenerator" \
		--add-data "resources:resources" \
		--add-data "src/config/defaults.toml:src/config" \
		--hidden-import tomli_w \
		--hidden-import defusedxml \
		--hidden-import httpx \
		--hidden-import keyring \
		--hidden-import edge_tts \
		--hidden-import customtkinter \
		--hidden-import PIL \
		--hidden-import cryptography \
		--hidden-import lxml \
		--hidden-import tomli \
		--hidden-import structlog \
		--collect-all customtkinter \
		--collect-all PIL \
		--collect-all src \
		main.py

# Сборка для Linux с UPX сжатием
build-linux:
	$(VENV_PYINSTALLER) --onefile --windowed \
		--name "AudiobookGenerator" \
		--add-data "resources:resources" \
		--add-data "src/config/defaults.toml:src/config" \
		--hidden-import tomli_w \
		--hidden-import defusedxml \
		--hidden-import httpx \
		--hidden-import keyring \
		--hidden-import edge_tts \
		--hidden-import customtkinter \
		--hidden-import PIL \
		--hidden-import cryptography \
		--hidden-import lxml \
		--hidden-import tomli \
		--hidden-import structlog \
		--collect-all customtkinter \
		--collect-all PIL \
		--collect-all src \
		--upx-dir /usr/bin/upx \
		main.py

# Сборка для Windows (из Linux с cross-compilation или в Windows)
build-windows:
	$(VENV_PYINSTALLER) --onefile --windowed \
		--name "AudiobookGenerator.exe" \
		--add-data "resources;resources" \
		--add-data "src/config/defaults.toml;src/config" \
		--hidden-import tomli_w \
		--hidden-import defusedxml \
		--hidden-import httpx \
		--hidden-import keyring \
		--hidden-import edge_tts \
		--hidden-import customtkinter \
		--hidden-import PIL \
		--hidden-import cryptography \
		--hidden-import lxml \
		--hidden-import tomli \
		--hidden-import structlog \
		--collect-all customtkinter \
		--collect-all PIL \
		--collect-all src \
		--icon resources/icon.ico \
		main.py

# Очистка временных файлов
clean:
	rm -rf build/ dist/ *.spec
	rm -rf __pycache__ */__pycache__ */*/__pycache__
	rm -rf .pytest_cache
	rm -rf temp_audio

# Запуск тестов
test:
	$(VENV_PYTHON) -m pytest tests/ -v

# Линтинг
lint:
	$(VENV_PYTHON) -m flake8 src/ tests/
	$(VENV_PYTHON) -m mypy src/

# Установка spacy моделей
spacy-models:
	$(VENV_PYTHON) -m spacy download ru_core_news_sm
	$(VENV_PYTHON) -m spacy download en_core_web_sm
