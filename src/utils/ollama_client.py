import ollama
import asyncio
from typing import Dict, Any, List, Optional
from src.config import settings


class OllamaClient:
    """Client for interacting with Ollama models."""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Ollama client with error handling."""
        try:
            self.client = ollama.Client(host=self.base_url)
            # Test connection
            self.client.list()
        except Exception as e:
            print(f"⚠️  Failed to connect to Ollama at {self.base_url}")
            print(f"Error: {e}")
            print("🔧 Please ensure Ollama is installed and running:")
            print("   1. Install Ollama: https://ollama.com/download")
            print("   2. Start Ollama: ollama serve")
            print("   3. Or run: python setup_ollama.py")
            self.client = None
    
    def is_connected(self) -> bool:
        """Check if client is connected to Ollama."""
        if self.client is None:
            return False
        try:
            self.client.list()
            return True
        except:
            return False
    
    def reconnect(self) -> bool:
        """Attempt to reconnect to Ollama."""
        self._initialize_client()
        return self.is_connected()
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        if not self.is_connected():
            print("Failed to connect to Ollama. Please check that Ollama is downloaded, running and accessible. https://ollama.com/download")
            return []
        
        try:
            response = self.client.list()
            return response.get('models', [])
        except Exception as e:
            print(f"Error listing models: {e}")
            # Try to reconnect
            if self.reconnect():
                try:
                    response = self.client.list()
                    return response.get('models', [])
                except:
                    pass
            return []
    
    def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama."""
        if not self.is_connected():
            print(f"Cannot pull model {model_name}: Not connected to Ollama")
            return False
        
        try:
            # This will pull the model if it doesn't exist
            self.client.chat(model=model_name, messages=[{"role": "user", "content": "ping"}])
            return True
        except Exception as e:
            print(f"Error pulling model {model_name}: {e}")
            return False
    
    def chat(self, model: str, messages: List[Dict[str, str]], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Chat with a model."""
        if not self.is_connected():
            print(f"Cannot chat with model {model}: Not connected to Ollama")
            return {}
        
        try:
            response = self.client.chat(
                model=model,
                messages=messages,
                options=options or {}
            )
            return response
        except Exception as e:
            print(f"Error chatting with model {model}: {e}")
            return {}
    
    async def async_chat(self, model: str, messages: List[Dict[str, str]], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Asynchronously chat with a model."""
        if not self.is_connected():
            print(f"Cannot async chat with model {model}: Not connected to Ollama")
            return {}
        
        try:
            # Using asyncio to make the call non-blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.client.chat(
                    model=model,
                    messages=messages,
                    options=options or {}
                )
            )
            return response
        except Exception as e:
            print(f"Error asynchronously chatting with model {model}: {e}")
            return {}


class OllamaMonitor:
    """Monitor for Ollama server status and model performance."""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.client = OllamaClient(base_url)
    
    def check_server_status(self) -> bool:
        """Check if the Ollama server is running."""
        try:
            # Try to list models as a health check
            self.client.list_models()
            return True
        except Exception:
            return False
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        try:
            # Try to get model details
            response = self.client.client.show(model_name)
            return response
        except Exception as e:
            print(f"Error getting model info for {model_name}: {e}")
            return {}
    
    def monitor_resource_usage(self) -> Dict[str, Any]:
        """Monitor resource usage of the Ollama server."""
        # In a real implementation, this would connect to system monitoring
        # For now, we'll return a placeholder
        return {
            "cpu_usage": "N/A",
            "memory_usage": "N/A",
            "disk_usage": "N/A",
            "active_models": len(self.client.list_models())
        }


# Global instance for easy access
ollama_client = OllamaClient()
ollama_monitor = OllamaMonitor()