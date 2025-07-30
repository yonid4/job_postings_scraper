#!/usr/bin/env python3
"""
Flask application runner for the AI Job Qualification Screening System.

This script starts the Flask web server with proper configuration.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to Python path to import src modules
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from app_supabase import app, logger

if __name__ == '__main__':
    try:
        # Set Flask environment
        os.environ['FLASK_ENV'] = 'development'
        
        # Get port from environment or use default
        port = int(os.environ.get('PORT', 5000))
        
        logger.info(f"Starting Flask application on port {port}")
        logger.info("Access the application at: http://localhost:5000")
        
        # Start the Flask application
        app.run(
            host='0.0.0.0',
            port=port,
            debug=True,
            use_reloader=False  # Disable reloader to avoid duplicate initialization
        )
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1) 