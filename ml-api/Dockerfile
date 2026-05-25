FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy datasets and training script
COPY *.csv ./
COPY train_on_render.py .

# Train models during build (THIS CREATES COMPATIBLE MODELS)
RUN python train_on_render.py

# Copy the main app
COPY ml_api.py .
COPY start.py .

EXPOSE 10000

CMD ["gunicorn", "--timeout", "120", "--workers", "2", "--bind", "0.0.0.0:10000", "ml_api:app"]