FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ALL files including .pkl models
COPY *.pkl ./
COPY *.py ./

# Expose port
EXPOSE 8080

# Run the app
CMD ["gunicorn", "--timeout", "120", "--workers", "2", "--bind", "0.0.0.0:8080", "ml_api:app"]