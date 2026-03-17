import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from silo.security.vault import VaultManager

class TestVaultManager(unittest.TestCase):
    @patch('hvac.Client')
    def test_vault_configuration(self, mock_client):
        # Set env vars
        os.environ["VAULT_ADDR"] = "http://localhost:8200"
        os.environ["VAULT_TOKEN"] = "test-token"
        
        vm = VaultManager()
        self.assertTrue(vm.url == "http://localhost:8200")
        mock_client.assert_called_with(url="http://localhost:8200", token="test-token", namespace=None)

    @patch('hvac.Client')
    def test_get_secret_v2(self, mock_client):
        # Mock client behavior
        mock_instance = mock_client.return_value
        mock_instance.is_authenticated.return_value = True
        
        mock_response = {
            "data": {
                "data": {
                    "MY_KEY": "MY_VALUE"
                }
            }
        }
        mock_instance.secrets.kv.v2.read_secret_version.return_value = mock_response
        
        vm = VaultManager()
        vm.client = mock_instance
        
        val = vm.get_secret("MY_KEY")
        self.assertEqual(val, "MY_VALUE")
        mock_instance.secrets.kv.v2.read_secret_version.assert_called_with(
            path="silo", mount_point="secret"
        )

    @patch('hvac.Client')
    def test_get_secret_v1_fallback(self, mock_client):
        # Mock client behavior to fail V2 and succeed V1
        mock_instance = mock_client.return_value
        mock_instance.is_authenticated.return_value = True
        
        mock_instance.secrets.kv.v2.read_secret_version.side_effect = Exception("Not V2")
        
        mock_response = {
            "data": {
                "MY_KEY": "V1_VALUE"
            }
        }
        mock_instance.secrets.kv.v1.read_secret.return_value = mock_response
        
        vm = VaultManager()
        vm.client = mock_instance
        
        val = vm.get_secret("MY_KEY")
        self.assertEqual(val, "V1_VALUE")

if __name__ == '__main__':
    unittest.main()
