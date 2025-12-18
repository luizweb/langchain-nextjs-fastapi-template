#!/bin/bash

# Aguardar o PostgreSQL estar pronto
echo "Waiting for PostgreSQL..."
while ! nc -z fastapi-fullstack-starter_database 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

# Executar migrações
echo "Running migrations..."
uv run alembic upgrade head

# Executar o comando passado para o container (o CMD)
echo "Starting application..."
exec "$@" # Substitui bash pelo comando: uv run uvicorn ...