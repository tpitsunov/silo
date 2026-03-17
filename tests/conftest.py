import pytest
import os
import shutil
import tempfile
from pathlib import Path
import keyring
from keyring.backends.fail import Keyring

@pytest.fixture
def temp_silo_dir():
    """Create a temporary directory for SILO data to avoid polluting the user's home."""
    old_silo_dir = os.environ.get("SILO_DIR")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        os.environ["SILO_DIR"] = str(tmp_path)
        # We need to mock/patch SILO_DIR in the modules because it's often a module-level constant
        import silo.security.security
        import silo.core.hub
        import silo.security.secrets
        
        original_security_dir = silo.security.security.SILO_DIR
        original_credentials_file = silo.security.security.CREDENTIALS_FILE
        original_hub_dir = silo.core.hub.SILO_DIR
        
        silo.security.security.SILO_DIR = tmp_path
        silo.security.security.CREDENTIALS_FILE = tmp_path / "credentials.silo"
        silo.core.hub.SILO_DIR = tmp_path
        # Update other related dirs in hub
        silo.core.hub.HUB_DIR = tmp_path / "hub"
        silo.core.hub.SKILLS_DIR = silo.core.hub.HUB_DIR / "skills"
        silo.core.hub.VENV_DIR = silo.core.hub.HUB_DIR / "venvs"
        
        yield tmp_path
        
        # Restore (optional but good practice)
        silo.security.security.SILO_DIR = original_security_dir
        silo.core.hub.SILO_DIR = original_hub_dir
        if old_silo_dir:
            os.environ["SILO_DIR"] = old_silo_dir
        else:
            del os.environ["SILO_DIR"]

@pytest.fixture(autouse=True)
def mock_keyring():
    """Use a dictionary-based dummy keyring to avoid interacting with the OS keychain during tests."""
    class DummyKeyring(keyring.backend.KeyringBackend):
        priority = 1
        def __init__(self):
            self.passwords = {}
        def set_password(self, service, username, password):
            self.passwords[(service, username)] = password
        def get_password(self, service, username):
            return self.passwords.get((service, username))
        def delete_password(self, service, username):
            if (service, username) in self.passwords:
                del self.passwords[(service, username)]

    original_keyring = keyring.get_keyring()
    dummy = DummyKeyring()
    keyring.set_keyring(dummy)
    yield dummy
    keyring.set_keyring(original_keyring)
