#!/usr/bin/env python3
"""System startup script for MiniMart AI Inventory Management System."""

import subprocess
import sys
import os
import time
import requests
from pathlib import Path


def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'fastapi', 'uvicorn', 'sqlalchemy', 'langchain', 'langgraph',
        'openai', 'pandas', 'numpy', 'statsmodels', 'chromadb'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Please install them with: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are installed")
    return True


def check_environment():
    """Check environment configuration."""
    print("🔍 Checking environment configuration...")
    
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        print("Please copy env.example to .env and configure it")
        return False
    
    # Check for required environment variables
    required_vars = [
        'DATABASE_URL', 'OPENAI_API_KEY', 'SECRET_KEY'
    ]
    
    missing_vars = []
    with open(env_file) as f:
        content = f.read()
        for var in required_vars:
            if f"{var}=" not in content or f"{var}=your_" in content:
                missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing or unconfigured environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ Environment configuration is valid")
    return True


def initialize_database():
    """Initialize the database with sample data."""
    print("🗄️  Initializing database...")
    
    try:
        result = subprocess.run(
            ["python", "app/database/init_db.py"],
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ Database initialized successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Database initialization failed: {e.stderr}")
        return False


def start_backend():
    """Start the backend server."""
    print("🚀 Starting backend server...")
    
    try:
        # Start backend in background
        backend_process = subprocess.Popen([
            "uvicorn", "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
        
        # Wait for backend to start
        print("⏳ Waiting for backend to start...")
        for i in range(30):  # Wait up to 30 seconds
            try:
                response = requests.get("http://localhost:8000/health", timeout=1)
                if response.status_code == 200:
                    print("✅ Backend server is running on http://localhost:8000")
                    return backend_process
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
        
        print("❌ Backend server failed to start")
        backend_process.terminate()
        return None
        
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None


def start_frontend():
    """Start the frontend development server."""
    print("🎨 Starting frontend server...")
    
    frontend_path = Path("frontend")
    if not frontend_path.exists():
        print("⚠️  Frontend directory not found, skipping frontend startup")
        return None
    
    try:
        # Check if node_modules exists
        if not (frontend_path / "node_modules").exists():
            print("📦 Installing frontend dependencies...")
            subprocess.run(["npm", "install"], cwd=frontend_path, check=True)
        
        # Start frontend in background
        frontend_process = subprocess.Popen([
            "npm", "start"
        ], cwd=frontend_path)
        
        # Wait for frontend to start
        print("⏳ Waiting for frontend to start...")
        for i in range(60):  # Wait up to 60 seconds
            try:
                response = requests.get("http://localhost:3000", timeout=1)
                if response.status_code == 200:
                    print("✅ Frontend server is running on http://localhost:3000")
                    return frontend_process
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
        
        print("❌ Frontend server failed to start")
        frontend_process.terminate()
        return None
        
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None


def main():
    """Main startup function."""
    print("🚀 MiniMart AI Inventory Management System")
    print("=" * 50)
    
    # Change to project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Initialize database
    if not initialize_database():
        sys.exit(1)
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        sys.exit(1)
    
    # Start frontend
    frontend_process = start_frontend()
    
    print("\n" + "=" * 50)
    print("🎉 SYSTEM STARTED SUCCESSFULLY!")
    print("=" * 50)
    print("📱 Frontend: http://localhost:3000")
    print("🔧 Backend API: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("💚 Health Check: http://localhost:8000/health")
    print("\nPress Ctrl+C to stop the system")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down system...")
        
        if frontend_process:
            frontend_process.terminate()
            print("✅ Frontend stopped")
        
        if backend_process:
            backend_process.terminate()
            print("✅ Backend stopped")
        
        print("👋 System shutdown complete")


if __name__ == "__main__":
    main()
