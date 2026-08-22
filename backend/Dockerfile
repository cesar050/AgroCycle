FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    gdal-bin \
    libgdal-dev \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-xlib-2.0-0 \
    libffi-dev \
    libcairo2 \
    libgobject-2.0-0 \
    fonts-liberation \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/ml_models

EXPOSE 5000

ENV PYTHONPATH=/app
ENV FLASK_APP=app/main.py