FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.pkl ./
COPY *.py ./

# Run the fix script to re-save vectorizers
RUN python fix_on_render.py

EXPOSE 10000

CMD ["gunicorn", "--timeout", "120", "--workers", "2", "--bind", "0.0.0.0:10000", "ml_api:app"]