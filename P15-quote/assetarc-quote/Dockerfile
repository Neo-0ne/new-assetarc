FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential ca-certificates && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
    && pip install --no-cache-dir gunicorn
COPY . .
RUN useradd -m appuser
USER appuser
# If the service has PORT in .env/.env.example use that; else default 8080 is fine.
EXPOSE 0
# Gunicorn expects app:app; if your entry is different, add a tiny app.py that imports your real app.
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]
