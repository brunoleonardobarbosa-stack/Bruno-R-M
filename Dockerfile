FROM python:3.11-slim

# Instalar dependências necessárias para compilar pacotes se necessário
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expõe as portas do Backend e Frontend
EXPOSE 8000
EXPOSE 8501

# Inicia o backend FastAPI em background e o frontend Streamlit em foreground
CMD uvicorn backend.main:app --host 0.0.0.0 --port 8000 & streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0
