#!/usr/bin/env python3
"""
Startup script for the AI Job Qualification System Web Frontend.

This script launches the Flask web application with proper configuration.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Launch the web frontend."""
    print("🚀 Starting AI Job Qualification System Web Frontend...")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not (project_root / "frontend" / "app.py").exists():
        print("❌ Error: frontend/app.py not found!")
        print("   Make sure you're running this from the project root directory.")
        sys.exit(1)
    
    # Change to frontend directory
    os.chdir(project_root / "frontend")
    
    # Set environment variables
    os.environ.setdefault('FLASK_ENV', 'development')
    os.environ.setdefault('FLASK_DEBUG', '1')
    
    # Import and run the Flask app
    try:
        from frontend.app import app
        
        print("✅ System initialized successfully!")
        print("🌐 Starting web server...")
        print("📱 Open http://localhost:5000 in your browser")
        print("🔧 Press Ctrl+C to stop the server")
        print("=" * 60)
        
        app.run(
            debug=True,
            host='0.0.0.0',
            port=5000,
            use_reloader=False  # Disable reloader to avoid file path issues
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 