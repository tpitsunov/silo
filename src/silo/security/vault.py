import os
from typing import Optional
import hvac

class VaultManager:
    """
    Manages interaction with HashiCorp Vault for secret retrieval.
    """
    def __init__(self):
        self.url = os.environ.get("VAULT_ADDR")
        self.token = os.environ.get("VAULT_TOKEN")
        self.namespace = os.environ.get("VAULT_NAMESPACE")
        self.client: Optional[hvac.Client] = None

        if self.url and self.token:
            self.client = hvac.Client(url=self.url, token=self.token, namespace=self.namespace)

    def is_configured(self) -> bool:
        """Checks if Vault is configured and potentially authenticated."""
        if self.client is None:
            return False
        return self.client.is_authenticated()

    def get_secret(self, key: str, mount_point: str = "secret") -> Optional[str]:
        """
        Retrieves a secret from Vault KV engine.
        Assumes the secret is stored in a path corresponding to the key or a common path.
        For SILO, we might look into a specific path like 'silo/secrets' or similar.
        """
        if not self.is_configured() or self.client is None:
            return None

        try:
            # Default to KV V2
            # We assume secrets are stored under silo/data/key or similar
            # For simplicity, we'll try to get it from 'silo' path if it exists
            read_response = self.client.secrets.kv.v2.read_secret_version(
                path="silo",
                mount_point=mount_point
            )
            data = read_response.get("data", {}).get("data", {})
            return data.get(key)
        except Exception:
            # Fallback to KV V1 or other errors
            try:
                read_response = self.client.secrets.kv.v1.read_secret(
                    path="silo",
                    mount_point=mount_point
                )
                data = read_response.get("data", {})
                return data.get(key)
            except Exception:
                return None
