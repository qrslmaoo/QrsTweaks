from __future__ import annotations
import base64
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict

from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

class VaultError(Exception):
    pass

@dataclass
class _Header:
    kdf_salt: bytes
    nonce: bytes

class Vault:
    """
    Local-only encrypted vault:
    - File format: JSON with base64 fields
    - Key derivation: scrypt
    - Encryption: AES-GCM (AEAD)
    """
    def __init__(self, path: Path):
        self.path = Path(path)
        self._key = None
        self._entries: List[Dict[str, str]] = []
        self.is_open = False
        self._header: _Header | None = None

    def unlock_or_create(self, password: str) -> bool:
        created = False
        if not self.path.exists():
            created = True
            self._header = _Header(kdf_salt=os.urandom(16), nonce=os.urandom(12))
            self._key = self._derive_key(password, self._header.kdf_salt)
            self._entries = []
            self.save()
        else:
            meta = json.loads(self.path.read_text(encoding="utf-8"))
            salt = base64.b64decode(meta["kdf_salt"])
            nonce = base64.b64decode(meta["nonce"])
            self._header = _Header(kdf_salt=salt, nonce=nonce)
            self._key = self._derive_key(password, salt)
            try:
                plaintext = self._decrypt(base64.b64decode(meta["ciphertext"]))
                self._entries = json.loads(plaintext.decode("utf-8"))
            except Exception:
                # Wrong password or corrupted file
                raise VaultError("Unable to unlock vault (wrong password or corrupted file).")
        self.is_open = True
        return created

    def add_entry(self, title: str, username: str, password: str):
        if not self.is_open:
            raise VaultError("Vault is locked.")
        if not title:
            raise VaultError("Title required.")
        self._entries.append({"title": title, "username": username, "password": password})

    def list_entries(self) -> List[Dict[str, str]]:
        if not self.is_open:
            return []
        return list(self._entries)

    def save(self):
        if not self.is_open or not self._header:
            raise VaultError("Vault not open.")
        data = json.dumps(self._entries, ensure_ascii=False).encode("utf-8")
        ct = self._encrypt(data)
        meta = {
            "kdf": "scrypt",
            "kdf_salt": base64.b64encode(self._header.kdf_salt).decode("ascii"),
            "nonce": base64.b64encode(self._header.nonce).decode("ascii"),
            "cipher": "AESGCM",
            "ciphertext": base64.b64encode(ct).decode("ascii"),
            "version": 1
        }
        self.path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    def export_csv(self, out_path: Path) -> int:
        if not self.is_open:
            raise VaultError("Vault not open.")
        rows = self._entries
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Title", "Username", "Password"])
            for r in rows:
                writer.writerow([r["title"], r["username"], r["password"]])
        return len(rows)

    # --- crypto primitives ---
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        kdf = Scrypt(salt=salt, length=32, n=2**14, r=8, p=1)
        return kdf.derive(password.encode("utf-8"))

    def _encrypt(self, plaintext: bytes) -> bytes:
        assert self._header and self._key
        aes = AESGCM(self._key)
        return aes.encrypt(self._header.nonce, plaintext, None)

    def _decrypt(self, ciphertext: bytes) -> bytes:
        assert self._header and self._key
        aes = AESGCM(self._key)
        return aes.decrypt(self._header.nonce, ciphertext, None)
