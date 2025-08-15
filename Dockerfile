# Use Python 3.9 slim image
FROM python:3.9-slim

# Install system dependencies for Chrome and Selenium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/googlechrome-linux-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/googlechrome-linux-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN CHROME_DRIVER_VERSION=$(curl -sS https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_STABLE) \
    && wget -O /tmp/chromedriver.zip https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/$CHROME_DRIVER_VERSION/linux64/chromedriver-linux64.zip \
    && unzip /tmp/chromedriver.zip -d /tmp/ \
    && mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/ \
    && rm -rf /tmp/chromedriver* \
    && chmod +x /usr/local/bin/chromedriver

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional scraping dependencies  
RUN pip install selenium beautifulsoup4 requests

# Copy application code (api, src folders)
COPY api/ ./api/
COPY src/ ./src/

# Create startup script inline
RUN echo '#!/usr/bin/env python3\n\
import os\n\
import subprocess\n\
import sys\n\
\n\
def main():\n\
    port = os.environ.get("PORT", "8000")\n\
    try:\n\
        port_num = int(port)\n\
        if port_num < 1 or port_num > 65535:\n\
            raise ValueError("Port out of range")\n\
    except ValueError:\n\
        print(f"Warning: Invalid PORT {port}, using default 8000")\n\
        port = "8000"\n\
    \n\
    cmd = ["uvicorn", "api.working_main:app", "--host", "0.0.0.0", "--port", str(port)]\n\
    print(f"Starting uvicorn on port {port}...")\n\
    print(f"Command: {\" \".join(cmd)}")\n\
    \n\
    try:\n\
        subprocess.run(cmd, check=True)\n\
    except subprocess.CalledProcessError as e:\n\
        print(f"Error starting uvicorn: {e}")\n\
        sys.exit(1)\n\
    except KeyboardInterrupt:\n\
        print("Shutting down...")\n\
        sys.exit(0)\n\
\n\
if __name__ == "__main__":\n\
    main()' > start.py && chmod +x start.py

# Set environment variables
ENV PYTHONPATH=/app
ENV DISPLAY=:99

# Expose port (Railway will provide $PORT environment variable)
EXPOSE 8000

# Start command with Python script that handles port
CMD ["python3", "start.py"]