FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Run the model creation script
RUN python create_models.py

# Verify models were created
RUN ls -la *.pkl

EXPOSE 10000

CMD ["gunicorn", "--timeout", "120", "--workers", "2", "--bind", "0.0.0.0:10000", "ml_api:app"]