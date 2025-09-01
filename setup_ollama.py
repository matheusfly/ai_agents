#!/usr/bin/env python3
"""
Automated setup script for Ollama installation and configuration.
"""
import os
import sys
import subprocess
import requests
import time
import platform
from pathlib import Path


class OllamaSetup:
    """Handles Ollama installation and setup."""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.ollama_url = "http://localhost:11434"
        self.required_models = ["qwen2.5:7b", "gemma2:9b"]
        
    def check_ollama_installed(self) -> bool:
        """Check if Ollama is installed."""
        try:
            result = subprocess.run(["ollama", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def check_ollama_running(self) -> bool:
        """Check if Ollama server is running."""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def install_ollama(self):
        """Install Ollama based on the operating system."""
        print("🚀 Installing Ollama...")
        
        if self.system == "windows":
            self._install_ollama_windows()
        elif self.system == "darwin":  # macOS
            self._install_ollama_macos()
        elif self.system == "linux":
            self._install_ollama_linux()
        else:
            print(f"❌ Unsupported operating system: {self.system}")
            sys.exit(1)
    
    def _install_ollama_windows(self):
        """Install Ollama on Windows."""
        print("📥 Downloading Ollama for Windows...")
        
        # Download Ollama installer
        download_url = "https://ollama.com/download/windows"
        installer_path = Path("ollama_installer.exe")
        
        try:
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            with open(installer_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print("⚡ Running Ollama installer...")
            print("📝 Please follow the installation wizard that opens.")
            print("⏳ After installation, press Enter to continue...")
            
            # Run the installer
            subprocess.Popen([str(installer_path)], shell=True)
            input()  # Wait for user to complete installation
            
            # Clean up
            if installer_path.exists():
                installer_path.unlink()
                
        except Exception as e:
            print(f"❌ Error downloading Ollama: {e}")
            print("🔗 Please manually download and install Ollama from: https://ollama.com/download")
            sys.exit(1)
    
    def _install_ollama_macos(self):
        """Install Ollama on macOS."""
        print("🍎 Installing Ollama on macOS...")
        
        try:
            # Try Homebrew first
            subprocess.run(["brew", "--version"], check=True, capture_output=True)
            print("🍺 Installing via Homebrew...")
            subprocess.run(["brew", "install", "ollama"], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to curl installation
            print("📥 Installing via curl...")
            subprocess.run(["curl", "-fsSL", "https://ollama.com/install.sh"], 
                         shell=True, check=True)
    
    def _install_ollama_linux(self):
        """Install Ollama on Linux."""
        print("🐧 Installing Ollama on Linux...")
        
        try:
            subprocess.run([
                "curl", "-fsSL", "https://ollama.com/install.sh", "|", "sh"
            ], shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing Ollama: {e}")
            sys.exit(1)
    
    def start_ollama_service(self):
        """Start the Ollama service."""
        print("🔄 Starting Ollama service...")
        
        if self.system == "windows":
            # On Windows, Ollama should start automatically after installation
            # If not, try to start it manually
            try:
                subprocess.Popen(["ollama", "serve"], shell=True)
            except Exception as e:
                print(f"⚠️  Could not start Ollama service: {e}")
                print("🔧 Please start Ollama manually by running 'ollama serve' in a new terminal")
        else:
            # On Unix-like systems
            try:
                subprocess.Popen(["ollama", "serve"])
            except Exception as e:
                print(f"⚠️  Could not start Ollama service: {e}")
                print("🔧 Please start Ollama manually by running 'ollama serve' in a new terminal")
        
        # Wait for service to start
        print("⏳ Waiting for Ollama service to start...")
        for i in range(30):  # Wait up to 30 seconds
            if self.check_ollama_running():
                print("✅ Ollama service is running!")
                return True
            time.sleep(1)
            print(f"⏳ Still waiting... ({i+1}/30)")
        
        print("❌ Ollama service failed to start within 30 seconds")
        return False
    
    def pull_required_models(self):
        """Pull required models."""
        if not self.check_ollama_running():
            print("❌ Ollama service is not running. Cannot pull models.")
            return False
        
        print("📦 Pulling required models...")
        
        for model in self.required_models:
            print(f"📥 Pulling {model}...")
            try:
                result = subprocess.run(
                    ["ollama", "pull", model], 
                    capture_output=True, text=True, timeout=600  # 10 minute timeout
                )
                
                if result.returncode == 0:
                    print(f"✅ Successfully pulled {model}")
                else:
                    print(f"❌ Failed to pull {model}: {result.stderr}")
                    # Try alternative model names
                    alt_model = self._get_alternative_model(model)
                    if alt_model:
                        print(f"🔄 Trying alternative: {alt_model}")
                        alt_result = subprocess.run(
                            ["ollama", "pull", alt_model],
                            capture_output=True, text=True, timeout=600
                        )
                        if alt_result.returncode == 0:
                            print(f"✅ Successfully pulled {alt_model}")
                        else:
                            print(f"❌ Failed to pull {alt_model}: {alt_result.stderr}")
                            
            except subprocess.TimeoutExpired:
                print(f"⏰ Timeout pulling {model}. This is normal for large models.")
                print("🔄 Model pull is continuing in the background.")
            except Exception as e:
                print(f"❌ Error pulling {model}: {e}")
        
        return True
    
    def _get_alternative_model(self, model: str) -> str:
        """Get alternative model name if the primary fails."""
        alternatives = {
            "qwen2.5:7b": "qwen2:7b",
            "gemma2:9b": "gemma:7b"
        }
        return alternatives.get(model)
    
    def verify_setup(self) -> bool:
        """Verify that Ollama is properly set up."""
        print("🔍 Verifying Ollama setup...")
        
        # Check if Ollama is installed
        if not self.check_ollama_installed():
            print("❌ Ollama is not installed")
            return False
        
        # Check if Ollama is running
        if not self.check_ollama_running():
            print("❌ Ollama service is not running")
            return False
        
        # Check available models
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model["name"] for model in models]
                print(f"📋 Available models: {model_names}")
                
                # Check if we have at least one working model
                if len(model_names) > 0:
                    print("✅ Ollama setup verified successfully!")
                    return True
                else:
                    print("⚠️  No models found. You may need to pull some models.")
                    return False
            else:
                print(f"❌ Error checking models: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error verifying setup: {e}")
            return False
    
    def create_test_script(self):
        """Create a test script to verify Ollama functionality."""
        test_script = '''#!/usr/bin/env python3
"""
Test script to verify Ollama functionality.
"""
import requests
import json

def test_ollama():
    """Test Ollama API."""
    try:
        # Test server health
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            print("❌ Ollama server is not responding")
            return False
        
        models = response.json().get("models", [])
        if not models:
            print("⚠️  No models available")
            return False
        
        print(f"✅ Found {len(models)} models:")
        for model in models:
            print(f"  - {model['name']}")
        
        # Test a simple chat request
        model_name = models[0]["name"]
        print(f"🧪 Testing chat with {model_name}...")
        
        chat_data = {
            "model": model_name,
            "messages": [{"role": "user", "content": "Say hello in one word"}],
            "stream": False
        }
        
        response = requests.post(
            "http://localhost:11434/api/chat",
            json=chat_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            message = result.get("message", {}).get("content", "")
            print(f"✅ Chat test successful! Response: {message}")
            return True
        else:
            print(f"❌ Chat test failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Ollama setup...")
    success = test_ollama()
    if success:
        print("🎉 Ollama is working correctly!")
    else:
        print("❌ Ollama test failed")
'''
        
        with open("test_ollama.py", "w") as f:
            f.write(test_script)
        
        print("📝 Created test_ollama.py - run this to test your Ollama setup")
    
    def run_setup(self):
        """Run the complete setup process."""
        print("🎯 Starting Ollama Setup...")
        print("=" * 50)
        
        # Check if already installed and running
        if self.check_ollama_installed() and self.check_ollama_running():
            print("✅ Ollama is already installed and running!")
            if self.verify_setup():
                print("🎉 Setup is complete!")
                return True
        
        # Install Ollama if not installed
        if not self.check_ollama_installed():
            self.install_ollama()
            
            # Verify installation
            if not self.check_ollama_installed():
                print("❌ Ollama installation failed")
                return False
        
        # Start Ollama service
        if not self.check_ollama_running():
            if not self.start_ollama_service():
                print("❌ Failed to start Ollama service")
                print("🔧 Please start Ollama manually by running 'ollama serve'")
                return False
        
        # Pull required models
        self.pull_required_models()
        
        # Verify setup
        success = self.verify_setup()
        
        # Create test script
        self.create_test_script()
        
        if success:
            print("\n🎉 Ollama setup completed successfully!")
            print("🚀 You can now run your Multi-Agent system!")
            print("🧪 Run 'python test_ollama.py' to test the setup")
        else:
            print("\n❌ Setup completed with issues")
            print("🔧 Please check the error messages above")
        
        return success


def main():
    """Main function."""
    print("🤖 Ollama Setup Assistant")
    print("=" * 30)
    
    setup = OllamaSetup()
    success = setup.run_setup()
    
    if success:
        print("\n✨ Next steps:")
        print("1. Run 'python test_ollama.py' to verify setup")
        print("2. Run 'python start_system.py' to start your Multi-Agent system")
    else:
        print("\n🆘 If you're still having issues:")
        print("1. Visit https://ollama.com for manual installation")
        print("2. Make sure to run 'ollama serve' to start the service")
        print("3. Pull at least one model: 'ollama pull llama2'")


if __name__ == "__main__":
    main()
