import json
from pathlib import Path
from cryptography.fernet import Fernet


class PasswordVault:
    """
    Simple encrypted password vault for QrsTweaks.
    Stores entries as { site: { user, password } }
    Encrypted using a master key.
    """

    def __init__(self):
        self.file = Path.home() / ".qrs_vault"
        self.key = None
        self.data = {}

    # ---------- INTERNAL ----------
    def _get_cipher(self):
        return Fernet(self.key)

    def _save(self):
        cipher = self._get_cipher()
        raw = json.dumps(self.data).encode()
        encrypted = cipher.encrypt(raw)
        self.file.write_bytes(encrypted)

    # ---------- PUBLIC ----------
    def load_or_create(self, master_key: str):
        self.key = Fernet(master_key.encode().ljust(32, b"0")[:32])

        if not self.file.exists():
            self.data = {}
            self._save()
            return

        encrypted = self.file.read_bytes()
        cipher = self._get_cipher()
        decrypted = cipher.decrypt(encrypted)
        self.data = json.loads(decrypted.decode())

    def add_entry(self, site: str, user: str, password: str):
        self.data[site] = {"user": user, "password": password}
        self._save()

    def list_entries(self):
        return self.data
