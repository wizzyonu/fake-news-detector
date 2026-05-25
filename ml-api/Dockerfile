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

# Copy ALL Python files
COPY *.py ./

# Copy ALL .pkl files (models and vectorizers)
COPY *.pkl ./

# Debug: List files to verify they were copied
RUN echo "=== Verifying .pkl files in /app ===" && \
    ls -la *.pkl && \
    echo "=== Total files in /app ===" && \
    ls -la

EXPOSE 10000

CMD ["gunicorn", "--timeout", "120", "--workers", "2", "--bind", "0.0.0.0:10000", "ml_api:app"]