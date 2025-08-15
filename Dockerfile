# Use Python 3.9 slim image - Railway rebuild v2
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

# Create a simple startup script that debugs the PORT variable
RUN echo '#!/bin/bash\n\
echo "=== Railway Environment Debug ==="\n\
echo "PORT environment variable: [$PORT]"\n\
echo "All environment variables:"\n\
printenv | grep -E "(PORT|RAILWAY)" || echo "No PORT/RAILWAY vars found"\n\
echo "================================"\n\
\n\
# Set default port if PORT is empty or invalid\n\
if [ -z "$PORT" ] || ! [[ "$PORT" =~ ^[0-9]+$ ]]; then\n\
    echo "PORT is empty or invalid, using 8000"\n\
    export PORT=8000\n\
fi\n\
\n\
echo "Starting uvicorn on port: $PORT"\n\
exec uvicorn api.working_main:app --host 0.0.0.0 --port $PORT\n\
' > start.sh && chmod +x start.sh

# Set environment variables
ENV PYTHONPATH=/app
ENV DISPLAY=:99

# Expose port (Railway will provide $PORT environment variable)
EXPOSE 8000

# Start command with hardcoded port (Railway will proxy to external port)
CMD ["uvicorn", "api.working_main:app", "--host", "0.0.0.0", "--port", "8000"]