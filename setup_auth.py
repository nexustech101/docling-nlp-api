#!/usr/bin/env python3
"""
Setup script for installing authentication dependencies and initializing the system.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True
        )
        print(f"✅ {description} completed successfully")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return None


def main():
    """Main setup function."""
    print("🚀 Setting up Docling NLP API Authentication System")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python version: {sys.version}")
    
    # Change to the app directory
    app_dir = Path(__file__).parent / "app"
    if not app_dir.exists():
        print("❌ App directory not found")
        sys.exit(1)
    
    os.chdir(app_dir)
    print(f"📂 Working directory: {app_dir}")
    
    # Install dependencies
    print("\n📦 Installing Dependencies")
    print("-" * 30)
    
    dependencies = [
        "firebase-admin",
        "slowapi",
        "redis",
        "python-multipart",  # Already in requirements but ensuring it's there
    ]
    
    for dep in dependencies:
        run_command(f"pip install {dep}", f"Installing {dep}")
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("\n🔧 Setting up environment configuration")
        print("-" * 40)
        
        # Copy example to .env
        with open(env_example, 'r') as src, open(env_file, 'w') as dst:
            content = src.read()
            # Generate a random JWT secret key
            import secrets
            jwt_secret = secrets.token_urlsafe(64)
            content = content.replace(
                'JWT_SECRET_KEY="your-super-secret-jwt-key-change-in-production"',
                f'JWT_SECRET_KEY="{jwt_secret}"'
            )
            dst.write(content)
        
        print("✅ Created .env file from template")
        print("⚠️  Please update Firebase configuration in .env file")
    elif env_file.exists():
        print("✅ .env file already exists")
    else:
        print("❌ No .env.example file found")
    
    # Test Redis connection (optional)
    print("\n🔗 Testing Redis Connection")
    print("-" * 30)
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        print("✅ Redis is available")
    except Exception as e:
        print(f"⚠️  Redis not available: {e}")
        print("   Rate limiting will use in-memory storage")
        print("   For production, install Redis:")
        print("   - Docker: docker run -d -p 6379:6379 redis:alpine")
        print("   - Windows: https://redis.io/download")
        print("   - macOS: brew install redis")
        print("   - Linux: sudo apt-get install redis-server")
    
    # Initialize database
    print("\n🗄️  Initializing Database")
    print("-" * 25)
    
    try:
        # Import and run database initialization
        sys.path.append('.')
        from utils.db import init_db
        from services.api_token_service import get_api_token_service
        
        init_db()
        print("✅ Database initialized")
        
        # Initialize API token service (creates tables)
        get_api_token_service()
        print("✅ API token service initialized")
        
    except Exception as e:
        print(f"⚠️  Database initialization warning: {e}")
    
    # Provide next steps
    print("\n🎉 Setup Complete!")
    print("=" * 20)
    print("\nNext Steps:")
    print("1. Configure Firebase (if needed):")
    print("   - Create Firebase project at https://console.firebase.google.com")
    print("   - Enable Authentication")
    print("   - Download service account key")
    print("   - Update FIREBASE_* variables in .env")
    print("\n2. Start Redis (if not already running):")
    print("   docker run -d -p 6379:6379 redis:alpine")
    print("\n3. Start the API server:")
    print("   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    print("\n4. Visit http://localhost:8000/docs to see the API documentation")
    print("\n📚 Read AUTHENTICATION.md for detailed setup instructions")


if __name__ == "__main__":
    main()
