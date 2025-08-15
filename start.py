#!/usr/bin/env python3
"""
Railway startup script that handles port configuration
"""
import os
import subprocess
import sys

def main():
    # Get port from environment variable, default to 8000
    port = os.environ.get('PORT', '8000')
    
    # Validate port is a number
    try:
        port_num = int(port)
        if port_num < 1 or port_num > 65535:
            raise ValueError("Port out of range")
    except ValueError:
        print(f"Warning: Invalid PORT '{port}', using default 8000")
        port = '8000'
    
    # Build uvicorn command
    cmd = [
        'uvicorn',
        'api.working_main:app',
        '--host', '0.0.0.0',
        '--port', str(port)
    ]
    
    print(f"Starting uvicorn on port {port}...")
    print(f"Command: {' '.join(cmd)}")
    
    # Start uvicorn
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting uvicorn: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        sys.exit(0)

if __name__ == '__main__':
    main()