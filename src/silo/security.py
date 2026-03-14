import os
import json
import base64
import keyring
from pathlib import Path
from typing import Dict, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

SILO_DIR = Path.home() / ".silo"
CREDENTIALS_FILE = SILO_DIR / "credentials.silo"

class SecurityManager:
    """
    Handles AES-256-GCM encryption for SILO secrets.
    """
    def __init__(self, master_key: Optional[str] = None):
        # 1. Resolve Master Key: Priority env > Keyring > Prompt/None
        self.master_key = master_key or os.environ.get("SILO_MASTER_KEY")
        if not self.master_key:
            self.master_key = keyring.get_password("silo", "master_key")
        
        if not self.master_key:
            # Generate a strong master key for this installation
            import secrets
            self.master_key = secrets.token_urlsafe(32)
            keyring.set_password("silo", "master_key", self.master_key)

    def _get_salt(self) -> bytes:
        """Get or generate a persistent unique salt for this installation."""
        salt_file = SILO_DIR / ".salt"
        if salt_file.exists():
            return salt_file.read_bytes()
        
        import secrets
        salt = secrets.token_bytes(16)
        SILO_DIR.mkdir(parents=True, exist_ok=True)
        salt_file.write_bytes(salt)
        return salt

    def _get_aes_gcm(self) -> AESGCM:
        # Derive a 256-bit key from the master key string and installation-specific salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._get_salt(),
            iterations=100000,
        )
        key = kdf.derive(self.master_key.encode())
        return AESGCM(key)

    def encrypt_secrets(self, secrets: Dict[str, str]) -> bytes:
        """Encrypt a dictionary of secrets using AES-GCM."""
        aesgcm = self._get_aes_gcm()
        nonce = os.urandom(12)
        data = json.dumps(secrets).encode()
        ciphertext = aesgcm.encrypt(nonce, data, None)
        # Store nonce + ciphertext
        return base64.b64encode(nonce + ciphertext)

    def decrypt_secrets(self, encrypted_data: bytes) -> Dict[str, str]:
        """Decrypt a dictionary of secrets using AES-GCM."""
        aesgcm = self._get_aes_gcm()
        raw_data = base64.b64decode(encrypted_data)
        nonce = raw_data[:12]
        ciphertext = raw_data[12:]
        decrypted_data = aesgcm.decrypt(nonce, ciphertext, None)
        return json.loads(decrypted_data.decode())

    def save_credentials(self, secrets: Dict[str, str]):
        """Save encrypted secrets to the hub's credentials file."""
        SILO_DIR.mkdir(parents=True, exist_ok=True)
        encrypted = self.encrypt_secrets(secrets)
        with open(CREDENTIALS_FILE, "wb") as f:
            f.write(encrypted)

    def load_credentials(self) -> Dict[str, str]:
        """Load and decrypt secrets from the hub's credentials file."""
        if not CREDENTIALS_FILE.exists():
            return {}
        with open(CREDENTIALS_FILE, "rb") as f:
            encrypted = f.read()
            try:
                return self.decrypt_secrets(encrypted)
            except Exception:
                return {}

    def set_desktop_secret(self, namespace: str, key: str, value: str):
        """Store a secret in the OS secure storage (Keychain)."""
        keyring.set_password("silo", f"{namespace}.{key}", value)

    def get_desktop_secret(self, namespace: str, key: str) -> Optional[str]:
        """Retrieve a secret from the OS secure storage (Keychain)."""
        return keyring.get_password("silo", f"{namespace}.{key}")

    def delete_desktop_secret(self, namespace: str, key: str):
        """Remove a secret from the OS secure storage (Keychain)."""
        try:
            keyring.delete_password("silo", f"{namespace}.{key}")
        except (keyring.errors.PasswordDeleteError, Exception):
            # Exception can happen if key doesn't exist or other OS-level issues
            pass
