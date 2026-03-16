import pytest
import os
import base64
from silo.security import SecurityManager

def test_security_manager_init(temp_silo_dir):
    """Test that SecurityManager initializes correctly and generates a master key."""
    sm = SecurityManager()
    assert sm.master_key is not None
    assert len(sm.master_key) >= 32

def test_encryption_decryption(temp_silo_dir):
    """Test standard AES-GCM encryption and decryption."""
    sm = SecurityManager(master_key="test-master-key")
    secrets = {"API_KEY": "sk-123456", "DB_PASSWORD": "password123"}
    
    encrypted = sm.encrypt_secrets(secrets)
    assert isinstance(encrypted, bytes)
    
    decrypted = sm.decrypt_secrets(encrypted)
    assert decrypted == secrets

def test_save_load_credentials(temp_silo_dir):
    """Test saving and loading encrypted credentials from file."""
    sm = SecurityManager(master_key="test-master-key")
    secrets = {"GITHUB_TOKEN": "ghp_secure_token"}
    
    sm.save_credentials(secrets)
    
    # Reload with a new instance using the same master key
    sm2 = SecurityManager(master_key="test-master-key")
    loaded = sm2.load_credentials()
    assert loaded == secrets

def test_salt_persistence(temp_silo_dir):
    """Test that the salt is persistent across instances."""
    sm1 = SecurityManager()
    salt1 = sm1._get_salt()
    
    sm2 = SecurityManager()
    salt2 = sm2._get_salt()
    
    assert salt1 == salt2

def test_file_permissions(temp_silo_dir):
    """Test that sensitive files have restricted permissions (on Unix)."""
    if os.name == 'nt':
        pytest.skip("File permission checks are Unix-specific")
        
    sm = SecurityManager()
    sm.save_credentials({"test": "data"})
    
    salt_file = temp_silo_dir / ".salt"
    credentials_file = temp_silo_dir / "credentials.silo"
    
    assert salt_file.exists()
    assert credentials_file.exists()
    
    # Check for 0o600 (read/write by owner only)
    assert oct(os.stat(salt_file).st_mode & 0o777) == '0o600'
    assert oct(os.stat(credentials_file).st_mode & 0o777) == '0o600'
