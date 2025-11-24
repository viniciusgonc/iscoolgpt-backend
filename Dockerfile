# =========================
# 1) Imagem base (builder)
# =========================
FROM python:3.12-slim AS builder

# Define a pasta de trabalho dentro do container
WORKDIR /app

# Copia apenas o requirements para instalar as dependências
COPY requirements.txt .

# Instala as dependências em modo "user" (dentro de /root/.local)
RUN pip install --user --no-cache-dir -r requirements.txt


# =========================
# 2) Imagem final (runtime)
# =========================
FROM python:3.12-slim

WORKDIR /app

# Copia as dependências instaladas no stage anterior
COPY --from=builder /root/.local /root/.local

# Garante que os binários instalados em /root/.local/bin estejam no PATH
ENV PATH=/root/.local/bin:$PATH

# Copia o código da aplicação para dentro da imagem
COPY app ./app

# Porta usada pelo Uvicorn dentro do container
EXPOSE 8000

# Comando para iniciar a API quando o container for iniciado
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
