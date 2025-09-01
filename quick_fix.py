#!/usr/bin/env python3
"""
Quick fix script for Ollama connection issues.
"""
import os
import sys
import subprocess
import platform
import time


def check_ollama_installed():
    """Check if Ollama is installed."""
    try:
        result = subprocess.run(["ollama", "--version"], 
                              capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except:
        return False


def check_ollama_running():
    """Check if Ollama is running."""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        return response.status_code == 200
    except:
        return False


def start_ollama():
    """Start Ollama service."""
    system = platform.system().lower()
    
    print("🔄 Starting Ollama service...")
    
    try:
        if system == "windows":
            # Try to start Ollama on Windows
            subprocess.Popen(["ollama", "serve"], shell=True, 
                           creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            # Unix-like systems
            subprocess.Popen(["ollama", "serve"])
        
        # Wait for service to start
        print("⏳ Waiting for Ollama to start...")
        for i in range(15):
            if check_ollama_running():
                print("✅ Ollama is now running!")
                return True
            time.sleep(1)
        
        print("⚠️  Ollama may be starting in the background...")
        return False
        
    except Exception as e:
        print(f"❌ Error starting Ollama: {e}")
        return False


def pull_basic_model():
    """Pull a basic model for testing."""
    print("📦 Pulling a basic model for testing...")
    
    try:
        # Try to pull a small, fast model
        result = subprocess.run(
            ["ollama", "pull", "llama3.2:1b"], 
            capture_output=True, text=True, timeout=300
        )
        
        if result.returncode == 0:
            print("✅ Successfully pulled llama3.2:1b model")
            return True
        else:
            print("⚠️  Failed to pull model, but Ollama should still work")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Model pull is taking longer than expected (this is normal)")
        print("🔄 The model will continue downloading in the background")
        return True
    except Exception as e:
        print(f"⚠️  Error pulling model: {e}")
        return False


def main():
    """Main quick fix function."""
    print("🚑 Quick Fix for Ollama Connection Issues")
    print("=" * 45)
    
    # Check if Ollama is installed
    if not check_ollama_installed():
        print("❌ Ollama is not installed!")
        print("🔧 Please install Ollama first:")
        print("   • Windows: Download from https://ollama.com/download")
        print("   • macOS: brew install ollama")
        print("   • Linux: curl -fsSL https://ollama.com/install.sh | sh")
        print("")
        print("💡 Or run: python setup_ollama.py for automated installation")
        return False
    
    print("✅ Ollama is installed")
    
    # Check if Ollama is running
    if check_ollama_running():
        print("✅ Ollama is already running!")
        print("🎉 Your system should work now!")
        return True
    
    print("⚠️  Ollama is not running")
    
    # Try to start Ollama
    if start_ollama():
        print("✅ Ollama started successfully!")
        
        # Try to pull a basic model
        pull_basic_model()
        
        print("\n🎉 Quick fix completed!")
        print("🚀 Your Multi-Agent system should now work!")
        print("📝 Run 'python start_system.py' to test")
        return True
    else:
        print("❌ Failed to start Ollama automatically")
        print("🔧 Please try manually:")
        print("   1. Open a new terminal/command prompt")
        print("   2. Run: ollama serve")
        print("   3. Keep that terminal open")
        print("   4. Run your system again")
        return False


if __name__ == "__main__":
    success = main()
    
    if not success:
        print("\n🆘 Still having issues?")
        print("💬 Common solutions:")
        print("   • Restart your terminal/command prompt")
        print("   • Check if port 11434 is available")
        print("   • Try running as administrator (Windows)")
        print("   • Check firewall settings")
        print("   • Run: python setup_ollama.py for full setup")
    
    input("\nPress Enter to exit...")
