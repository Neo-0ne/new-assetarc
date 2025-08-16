FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn
COPY . .
EXPOSE 5011
CMD ["gunicorn","-b","0.0.0.0:5011","app:app"]
