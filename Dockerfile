
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir fastapi uvicorn jinja2 python-multipart
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
