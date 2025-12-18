FROM python:3.12-slim

WORKDIR /app

# Instalar netcat para o health check do postgres
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Instalar uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copiar arquivos de dependências primeiro
COPY pyproject.toml uv.lock* ./

# Instalar dependências
RUN uv sync --frozen --no-dev --no-cache

# Copiar entrypoint
COPY ./entrypoint.sh /usr/src/app/entrypoint.sh
RUN chmod +x /usr/src/app/entrypoint.sh

# Copiar o resto do código
COPY . .

EXPOSE 8000

ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
CMD ["uv", "run", "uvicorn", "--host", "0.0.0.0", "app.app:app"]