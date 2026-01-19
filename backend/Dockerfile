FROM python:3.12-slim

WORKDIR /app

# Instalar netcat para o health check do postgres
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Instalar uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copiar arquivos de dependências primeiro
COPY pyproject.toml uv.lock* ./

ENV UV_LINK_MODE=copy

# Instalar dependências
RUN uv sync --frozen --no-dev

# Copiar entrypoint
COPY ./entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

# Copiar o restante do código
COPY . .

EXPOSE 8000

ENTRYPOINT ["bash", "/app/entrypoint.sh"]
CMD ["uv", "run", "uvicorn", "--host", "0.0.0.0", "app.main:app"]