FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema para psycopg2 y utilidades
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar requerimientos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Configurar variables de entorno para que Python encuentre los módulos
ENV PYTHONPATH=/app:/app/farmacruz_api
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Comando de arranque para FastAPI
CMD ["uvicorn", "farmacruz_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
