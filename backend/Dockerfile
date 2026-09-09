FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libgomp1 libsm6 libxrender1 libxext6 \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy the whole repo so parent-based path resolution (rules/, storage)
# works exactly as in local dev.
COPY . .

WORKDIR /app/backend

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && python -m seed.seed && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]