FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Create a startup script to ensure models load
RUN echo '#!/bin/bash\n\
echo "=== Starting ML API ==="\n\
echo "Python version: $(python --version)"\n\
echo "Numpy version: $(python -c \"import numpy; print(numpy.__version__)\" 2>/dev/null || echo 'Not installed')"\n\
echo "Files in directory: $(ls -la *.pkl 2>/dev/null | wc -l) pickle files"\n\
gunicorn --timeout 120 --workers 2 --bind 0.0.0.0:10000 ml_api:app' > /app/start.sh

RUN chmod +x /app/start.sh

EXPOSE 10000

CMD ["/app/start.sh"]