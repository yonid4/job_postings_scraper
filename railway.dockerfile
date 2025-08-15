FROM python:3.9-slim

WORKDIR /app

# Copy only what we need
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

# Copy application files
COPY backend/api ./api
COPY backend/src ./src

# Simple start
CMD ["python", "-m", "uvicorn", "api.working_main:app", "--host", "0.0.0.0", "--port", "8000"]