
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libcairo2 pango1.0-tools libpango-1.0-0 libpangoft2-1.0-0 libffi-dev libjpeg62-turbo libpng16-16 fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5010
CMD ["gunicorn","-b","0.0.0.0:5010","-w","3","app:app"]
