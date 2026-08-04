FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN addgroup --system mr9 && adduser --system --ingroup mr9 mr9 \
    && mkdir -p /var/lib/mr9/firmwares \
    && chown -R mr9:mr9 /app /var/lib/mr9
ENV PYTHONPATH=/app
EXPOSE 8000
USER mr9
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
