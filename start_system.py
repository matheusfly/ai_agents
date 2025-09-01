#!/usr/bin/env python3
"""
Script to start the Multi-Agent Prompt Engine system.
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


def start_websocket_server():
    """Start the WebSocket server."""
    print("Starting WebSocket server...")
    ws_process = subprocess.Popen([
        sys.executable, "websocket_server.py"
    ])
    return ws_process


def start_ui():
    """Start the Streamlit UI."""
    print("Starting Streamlit UI...")
    ui_process = subprocess.Popen([
        sys.executable, "-m", "streamlit",
        "run", "src/ui/dashboard.py"
    ])
    return ui_process


def main():
    """Main function to start the system."""
    print("Starting Multi-Agent Prompt Engine system...")

    # Start the API server
    api_process = start_api()

    # Start the WebSocket server
    ws_process = start_websocket_server()

    # Wait a moment for the servers to start
    time.sleep(5)

    # Start the UI
    ui_process = start_ui()

    print("\nSystem started successfully!")
    print("API available at: http://localhost:8000")
    print("WebSocket server available at: ws://localhost:3001")
    print("UI available at: http://localhost:8501")
    print("\nPress Ctrl+C to stop the system...")

    try:
        # Wait for all processes
        api_process.wait()
        ws_process.wait()
        ui_process.wait()
    except KeyboardInterrupt:
        print("\n\nStopping system...")
        api_process.terminate()
        ws_process.terminate()
        ui_process.terminate()
        api_process.wait()
        ws_process.wait()
        ui_process.wait()
        print("System stopped.")


if __name__ == "__main__":
    main()