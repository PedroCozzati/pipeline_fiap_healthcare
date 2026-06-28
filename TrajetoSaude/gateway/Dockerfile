FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

# No GCP (Cloud Run / GKE), as bibliotecas google-auth obtêm credenciais
# automaticamente via Application Default Credentials (metadata server).
# Localmente, monte o JSON e defina GOOGLE_APPLICATION_CREDENTIALS via .env.
CMD ["uvicorn", "app.main:api", "--host", "0.0.0.0", "--port", "8000"]
