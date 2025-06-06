"""
Setup script for REAL Voice Assistant.
This installs actual dependencies that actually work.
"""

import subprocess
import sys
import shutil
from pathlib import Path


def main():
    print("=== REAL Voice Assistant Setup ===\n")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8+ required")
        return False
    
    print(f"✓ Python {sys.version}")
    
    # Install dependencies
    print("\nInstalling dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed")
    except Exception as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False
    
    # Create .env from example
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("✓ Created .env file")
        print("\n⚠️  IMPORTANT: Edit .env and add your OpenAI API key!")
    
    print("\n=== Setup Complete ===")
    print("\nTo run the assistant:")
    print("1. Edit .env and add your OpenAI API key")
    print("2. Run: python main.py")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
