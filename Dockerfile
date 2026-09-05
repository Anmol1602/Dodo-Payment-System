FROM python:3.10-slim

WORKDIR /app
ENV PYTHONPATH=/app

# Install system dependencies for building python libraries and healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000 8001

CMD ["sh", "-c", "alembic upgrade head && python3 -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
