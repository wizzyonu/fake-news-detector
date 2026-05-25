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

# DELETE any existing .pkl files from the image (they are corrupted)
RUN rm -f *.pkl

# RUN TRAINING - This MUST happen during build
RUN python train_on_render.py

# Verify training created the files
RUN ls -la *.pkl

EXPOSE 10000

CMD ["gunicorn", "--timeout", "120", "--workers", "2", "--bind", "0.0.0.0:10000", "ml_api:app"]