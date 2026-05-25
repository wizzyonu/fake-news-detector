FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy everything first (including .pkl files)
COPY . .

# Verify files are copied
RUN echo "=== Checking for .pkl files ===" && \
    ls -la *.pkl 2>/dev/null || echo "No .pkl files found in root" && \
    echo "=== All files ===" && \
    ls -la

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 10000

CMD ["gunicorn", "--timeout", "120", "--workers", "2", "--bind", "0.0.0.0:10000", "ml_api:app"]