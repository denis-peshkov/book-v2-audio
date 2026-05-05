"""
Модуль безопасного хранения API-ключей.
Использует системный keyring, с резервным шифрованным файлом.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

SERVICE_NAME = "audiobook-generator"


class KeyManager:
    """Менеджер API-ключей.

    Приоритет: системный keyring.
    Резерв: зашифрованный файл с привязкой к машине.

    Пример использования:
        KeyManager.save_key("deepseek", "sk-...")
        key = KeyManager.load_key("deepseek")  # "sk-..."
    """

    KEY_FILE = Path.home() / ".audiobook-generator" / ".keys.enc"

    @staticmethod
    def save_key(provider: str, api_key: str) -> bool:
        """Сохранение API-ключа.

        Args:
            provider: Провайдер (deepseek, chatgpt, grok, qwen).
            api_key: Ключ API.

        Returns:
            True если ключ сохранён успешно.
        """
        # Пытаемся сохранить в системный keyring
        try:
            import keyring
            keyring.set_password(SERVICE_NAME, f"{provider}_api_key", api_key)
            logger.info("API-ключ сохранён в системный keyring: %s", provider)
            return True
        except (ImportError, Exception) as e:
            logger.warning("keyring недоступен (%s), использую зашифрованный файл", e)
            return KeyManager._save_fallback(provider, api_key)

    @staticmethod
    def load_key(provider: str) -> Optional[str]:
        """Загрузка API-ключа.

        Args:
            provider: Провайдер (deepseek, chatgpt, grok, qwen).

        Returns:
            Ключ API или None, если ключ не найден.
        """
        # Пытаемся загрузить из системного keyring
        try:
            import keyring
            key = keyring.get_password(SERVICE_NAME, f"{provider}_api_key")
            if key:
                return key
        except (ImportError, Exception) as e:
            logger.warning("keyring недоступен (%s), пробую зашифрованный файл", e)

        # Резерв: зашифрованный файл
        return KeyManager._load_fallback(provider)

    @staticmethod
    def delete_key(provider: str) -> bool:
        """Удаление API-ключа.

        Args:
            provider: Провайдер (deepseek, chatgpt, grok, qwen).

        Returns:
            True если ключ удалён успешно.
        """
        try:
            import keyring
            try:
                keyring.delete_password(SERVICE_NAME, f"{provider}_api_key")
            except keyring.errors.PasswordDeleteError:
                pass
        except ImportError:
            pass

        # Удаляем из зашифрованного файла
        return KeyManager._delete_fallback(provider)

    @staticmethod
    def _save_fallback(provider: str, api_key: str) -> bool:
        """Сохранение ключа в зашифрованный файл."""
        try:
            cipher = KeyManager._get_cipher()
            data = KeyManager._load_encrypted_data()
            data[provider] = api_key
            KeyManager.KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
            encrypted = cipher.encrypt(json.dumps(data).encode())
            KeyManager.KEY_FILE.write_bytes(encrypted)
            logger.info("API-ключ сохранён в зашифрованный файл: %s", provider)
            return True
        except Exception as e:
            logger.error("Ошибка сохранения ключа: %s", e)
            return False

    @staticmethod
    def _load_fallback(provider: str) -> Optional[str]:
        """Загрузка ключа из зашифрованного файла."""
        try:
            cipher = KeyManager._get_cipher()
            data = KeyManager._load_encrypted_data()
            return data.get(provider)
        except Exception as e:
            logger.error("Ошибка загрузки ключа: %s", e)
            return None

    @staticmethod
    def _delete_fallback(provider: str) -> bool:
        """Удаление ключа из зашифрованного файла."""
        try:
            cipher = KeyManager._get_cipher()
            data = KeyManager._load_encrypted_data()
            if provider in data:
                del data[provider]
                encrypted = cipher.encrypt(json.dumps(data).encode())
                KeyManager.KEY_FILE.write_bytes(encrypted)
            return True
        except Exception as e:
            logger.error("Ошибка удаления ключа: %s", e)
            return False

    @staticmethod
    def _get_cipher():
        """Получение шифра на основе machine ID."""
        from cryptography.fernet import Fernet

        machine_id = KeyManager._get_machine_id()
        key = base64.urlsafe_b64encode(
            hashlib.sha256(machine_id.encode()).digest()
        )
        return Fernet(key)

    @staticmethod
    def _get_machine_id() -> str:
        """Получение уникального идентификатора машины."""
        # Пробуем /etc/machine-id (Linux)
        try:
            machine_id_path = Path("/etc/machine-id")
            if machine_id_path.exists():
                return machine_id_path.read_text().strip()
        except IOError:
            pass

        # Пробуем /var/lib/dbus/machine-id
        try:
            dbus_path = Path("/var/lib/dbus/machine-id")
            if dbus_path.exists():
                return dbus_path.read_text().strip()
        except IOError:
            pass

        # Резерв: хостнейм + домашняя директория
        import socket
        return f"{socket.gethostname()}-{Path.home()}"

    @staticmethod
    def _load_encrypted_data() -> dict:
        """Загрузка расшифрованных данных из файла."""
        if not KeyManager.KEY_FILE.exists():
            return {}

        cipher = KeyManager._get_cipher()
        encrypted = KeyManager.KEY_FILE.read_bytes()
        decrypted = cipher.decrypt(encrypted)
        return json.loads(decrypted.decode())
