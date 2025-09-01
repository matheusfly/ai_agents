#!/usr/bin/env python3
"""
Script to start the Multi-Agent Prompt Engine system with debug dashboard.
"""
import subprocess
import sys
import time
import os


def start_api():
    """Start the FastAPI server."""
    print("Starting FastAPI server...")
    api_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", 
        "src.api.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000",
        "--reload"
    ])
    return api_process


def start_debug_ui():
    """Start the Debug Dashboard UI."""
    print("Starting Debug Dashboard UI...")
    ui_process = subprocess.Popen([
        sys.executable, "-m", "streamlit", 
        "run", "src/ui/debug_dashboard.py",
        "--server.port", "8501"
    ])
    return ui_process


def main():
    """Main function to start the system."""
    print("🔧 Starting Multi-Agent Prompt Engine with Debug Dashboard...")
    print("=" * 60)
    
    # Start the API server
    api_process = start_api()
    
    # Wait a moment for the API to start
    time.sleep(5)
    
    # Start the Debug UI
    ui_process = start_debug_ui()
    
    print("\n🎉 Debug System started successfully!")
    print("📡 API available at: http://localhost:8000")
    print("🔧 Debug Dashboard at: http://localhost:8501")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("\n🛠️  Debug Features:")
    print("  • Live system monitoring")
    print("  • Real-time Ollama process tracking")
    print("  • LangGraph workflow visualization")
    print("  • API call monitoring")
    print("  • Live log streaming")
    print("  • Prompt testing interface")
    print("\nPress Ctrl+C to stop the system...")
    
    try:
        # Wait for both processes
        api_process.wait()
        ui_process.wait()
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping debug system...")
        api_process.terminate()
        ui_process.terminate()
        api_process.wait()
        ui_process.wait()
        print("✅ Debug system stopped.")


if __name__ == "__main__":
    main()
