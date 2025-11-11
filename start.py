#!/usr/bin/env python3
import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False
    return True

def start_server():
    """Start the FastAPI server"""
    print("\n🚀 Starting LLM Document Query System...")
    print("📱 Web UI: http://localhost:8000")
    print("📚 API docs: http://localhost:8000/docs")
    print("🔑 Use your team token from .env file for authentication")
    print("\nPress Ctrl+C to stop the server\n")
    
    try:
        subprocess.run([sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"])
    except KeyboardInterrupt:
        print("\n👋 Server stopped!")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    if install_requirements():
        start_server()