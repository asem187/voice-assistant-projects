"""
Setup script for the Realtime Voice Assistant.
Handles installation, database setup, and configuration.
"""

import asyncio
import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Optional


def install_dependencies():
    """Install Python dependencies."""
    print("Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False


def setup_environment():
    """Set up environment configuration."""
    print("Setting up environment configuration...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✓ .env file already exists")
        return True
    
    if not env_example.exists():
        print("✗ .env.example not found")
        return False
    
    # Copy example to actual env file
    shutil.copy(env_example, env_file)
    
    print("✓ Created .env file from template")
    print("⚠️  Please edit .env file with your API keys and configuration")
    
    return True


def create_directories():
    """Create necessary directories."""
    print("Creating directories...")
    
    directories = [
        "data",
        "logs", 
        "temp",
        "models"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created directory: {directory}")
    
    return True


def check_system_requirements():
    """Check system requirements."""
    print("Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("✗ Python 3.8 or higher is required")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Check for required system tools
    tools_to_check = ["git"]
    
    for tool in tools_to_check:
        if shutil.which(tool) is None:
            print(f"⚠️  {tool} not found - some features may not work")
        else:
            print(f"✓ {tool} found")
    
    return True


async def setup_database():
    """Set up the database."""
    print("Setting up database...")
    
    try:
        # Import here to avoid import issues during setup
        from database import initialize_database
        from config import settings
        
        # Initialize database
        await initialize_database()
        print("✓ Database initialized successfully")
        return True
        
    except Exception as e:
        print(f"✗ Database setup failed: {e}")
        print("  You may need to set up PostgreSQL or update DATABASE_URL in .env")
        return False


def validate_configuration():
    """Validate the configuration."""
    print("Validating configuration...")
    
    try:
        from config import settings
        
        # Check essential settings
        if not settings.openai.api_key or settings.openai.api_key == "your_openai_api_key_here":
            print("⚠️  OpenAI API key not configured in .env file")
            return False
        
        if not settings.security.secret_key or settings.security.secret_key == "your-secret-key-here-32-chars-min":
            print("⚠️  Secret key not configured in .env file")
            return False
        
        print("✓ Configuration validated")
        return True
        
    except Exception as e:
        print(f"✗ Configuration validation failed: {e}")
        return False


async def main():
    """Main setup function."""
    print("🤖 Realtime Voice Assistant Setup")
    print("=" * 40)
    print("⚠️  WARNING: This project uses a FICTIONAL OpenAI Realtime API")
    print("   This setup will not work until OpenAI releases such an API")
    print("=" * 40)
    
    success = True
    
    # Step 1: Check system requirements
    if not check_system_requirements():
        success = False
    
    # Step 2: Create directories
    if not create_directories():
        success = False
    
    # Step 3: Install dependencies
    if not install_dependencies():
        success = False
    
    # Step 4: Setup environment
    if not setup_environment():
        success = False
    
    # Step 5: Validate configuration
    if not validate_configuration():
        print("\nPlease configure your .env file with:")
        print("- OPENAI_API_KEY: Your OpenAI API key")
        print("- SECRET_KEY: A secure random secret key")
        print("- DATABASE_URL: Your database connection string")
        success = False
    
    # Step 6: Setup database (if config is valid)
    if success:
        try:
            await setup_database()
        except Exception as e:
            print(f"Database setup skipped: {e}")
            print("You can run database setup later with: python -c 'import asyncio; from database import initialize_database; asyncio.run(initialize_database())'")
    
    print("\n" + "=" * 40)
    if success:
        print("✅ Setup completed successfully!")
        print("\nNOTE: This project is a CONCEPT and will not work until")
        print("OpenAI releases a Realtime API. For a working voice assistant,")
        print("use the 'real-voice-assistant' project instead.")
        print("\nNext steps (when API becomes available):")
        print("1. Edit .env file with your API keys")
        print("2. Run: python main.py")
    else:
        print("❌ Setup completed with warnings")
        print("Please resolve the issues above before running the application")
    
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Setup failed: {e}")
        sys.exit(1)
