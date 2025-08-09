FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libcairo2 pango1.0-tools libjpeg62-turbo libpng16-16 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 0
CMD ["gunicorn","-b","0.0.0.0:8080","-w","2","app:app"]
