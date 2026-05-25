FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything
COPY . .

# RUN THE TRAINING SCRIPT TO CREATE NEW MODELS
RUN echo "=== TRAINING MODELS ON RENDER ===" && \
    python train_on_render.py

# Verify models were created
RUN echo "=== VERIFYING MODELS ===" && \
    ls -la *.pkl && \
    python -c "import pickle; import joblib; import numpy as np; data = pickle.load(open('model_rf_retrained.pkl', 'rb')); print('✅ Random Forest model works')" && \
    python -c "import pickle; import joblib; import numpy as np; data = pickle.load(open('tfidf_vectorizer_retrained.pkl', 'rb')); print('✅ Vectorizer works')"

EXPOSE 10000

CMD ["gunicorn", "--timeout", "120", "--workers", "2", "--bind", "0.0.0.0:10000", "ml_api:app"]