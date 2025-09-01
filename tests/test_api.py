import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from api.main import app
from fastapi.testclient import TestClient


class TestAPI(unittest.TestCase):
    """Test cases for the FastAPI application."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        """Test the root endpoint."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.json())
    
    def test_health_endpoint(self):
        """Test the health check endpoint."""
        # Mock the ollama_monitor to avoid actual API calls
        with patch('src.api.main.ollama_monitor') as mock_monitor:
            mock_monitor.check_server_status.return_value = True
            mock_monitor.client.list_models.return_value = []
            
            response = self.client.get("/health")
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn("status", data)
            self.assertIn("ollama_server", data)
            self.assertIn("models", data)
    
    def test_models_endpoint(self):
        """Test the models endpoint."""
        # Mock the ollama_monitor to avoid actual API calls
        with patch('src.api.main.ollama_monitor') as mock_monitor:
            mock_monitor.client.list_models.return_value = [
                {"name": "qwen3:latest"},
                {"name": "gemma3:latest"},
                {"name": "llama3:latest"}
            ]
            
            response = self.client.get("/models")
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn("models", data)
            # We expect at least 2 models, but there might be more
            self.assertGreaterEqual(len(data["models"]), 2)


if __name__ == '__main__':
    unittest.main()