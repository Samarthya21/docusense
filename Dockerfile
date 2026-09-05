FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (build-essential, curl for health checks, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install lightweight python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt

# Copy application source code
COPY . .

# Expose ports (FastAPI on 8000, Streamlit on 8501)
EXPOSE 8000 8501

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
