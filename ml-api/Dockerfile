FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY *.pkl ./
COPY *.py ./

# Run the vectorizer fix script during build (THIS IS THE KEY)
RUN python fix_vectorizers_docker.py

# Verify vectorizers are fixed
RUN python -c "import pickle; import joblib; import numpy as np; data = joblib.load('tfidf_vectorizer.pkl'); print('✅ Vectorizer loaded successfully')"

EXPOSE 10000

CMD ["gunicorn", "--timeout", "120", "--workers", "2", "--bind", "0.0.0.0:10000", "ml_api:app"]