# Guia Docker - Desenvolvimento e Deploy

Este guia explica como usar Docker no projeto, seguindo boas práticas de desenvolvimento.

## Estrutura de Arquivos

```
├── docker-compose.yaml          # Orquestração de todos os serviços (raiz)
├── backend/
│   ├── Dockerfile              # Imagem do backend FastAPI
│   ├── entrypoint.sh           # Script de inicialização
│   ├── .env.local             # Env para desenvolvimento local
│   └── .env.docker            # Env para containers Docker
└── frontend/
    └── Dockerfile              # Imagem do frontend Next.js
```

## Arquivos de Ambiente

### `.env.local` (Desenvolvimento Local)
Usado quando você roda o **backend FORA do Docker**:
- PostgreSQL roda em container
- FastAPI roda na sua máquina
- Conexão: `localhost:5432`

```bash
# Copiar e renomear para uso
cp backend/.env.local backend/.env
```

### `.env.docker` (Containers Docker)
Usado quando você roda **TUDO em containers**:
- PostgreSQL, Backend e Frontend em containers
- Conexão: `database:5432` (rede Docker)

```bash
# Copiar e renomear para uso
cp backend/.env.docker backend/.env
```

## Cenários de Uso

### Cenário 1: Desenvolvimento Local (Recomendado)
**Quando usar**: Desenvolvimento diário, debug, testes rápidos

**PostgreSQL em Docker, Apps rodando localmente**

```bash
# 1. Configurar ambiente
cp backend/.env.local backend/.env

# 2. Subir apenas o banco de dados
docker compose up database -d

# 3. Rodar backend localmente
cd backend
uv sync
alembic upgrade head
task run

# 4. Rodar frontend localmente (em outro terminal)
cd frontend
npm install
npm run dev
```

**Vantagens**:
- Hot reload funciona perfeitamente
- Debug mais rápido
- Menor uso de recursos
- Ideal para migrations com Alembic

**Acessos**:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- PostgreSQL: localhost:5432

---

### Cenário 2: Tudo em Containers
**Quando usar**: Simular produção, testar integração completa, deploy

**Backend, Frontend e PostgreSQL em containers**

```bash
# 1. Configurar ambiente
cp backend/.env.docker backend/.env

# 2. Subir todos os serviços
docker compose up -d

# 3. Ver logs
docker compose logs -f

# 4. Parar todos os serviços
docker compose down
```

**Vantagens**:
- Ambiente idêntico ao de produção
- Testa integração completa
- Isolamento total

**Acessos**:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- PostgreSQL: localhost:5432 (porta exposta)

---

### Cenário 3: Apenas Banco de Dados
**Quando usar**: Rodar migrations, testes de banco, exploração

```bash
# Subir apenas PostgreSQL
docker compose up database -d

# Conectar via psql
docker exec -it langchain-nextjs-fastapi_database psql -U app_user -d app_db

# Parar
docker compose down
```

---

## Comandos Úteis

### Gerenciar Serviços

```bash
# Subir todos os serviços
docker compose up -d

# Subir apenas um serviço específico
docker compose up database -d
docker compose up backend -d
docker compose up frontend -d

# Ver logs em tempo real
docker compose logs -f
docker compose logs -f backend
docker compose logs -f frontend

# Parar serviços (mantém volumes)
docker compose down

# Parar e remover volumes (apaga dados do banco!)
docker compose down -v

# Rebuild de imagens
docker compose build
docker compose build backend
docker compose build frontend

# Rebuild e subir
docker compose up -d --build
```

### Executar Comandos nos Containers

```bash
# Backend - Rodar migrations
docker compose exec backend uv run alembic upgrade head

# Backend - Shell interativo
docker compose exec backend bash

# Frontend - Shell interativo
docker compose exec frontend sh

# PostgreSQL - Acessar banco
docker compose exec database psql -U app_user -d app_db
```

### Debug e Inspeção

```bash
# Ver status dos containers
docker compose ps

# Ver uso de recursos
docker stats

# Inspecionar logs de erro
docker compose logs backend | grep ERROR
docker compose logs frontend | grep error

# Restart de um serviço específico
docker compose restart backend
docker compose restart frontend
```

---

## Fluxo de Trabalho Recomendado

### Dia a Dia (Desenvolvimento)

```bash
# Manhã: iniciar trabalho
cp backend/.env.local backend/.env
docker compose up database -d
cd backend && task run  # Terminal 1
cd frontend && npm run dev  # Terminal 2

# Fim do dia
# Não precisa parar o database (pode deixar rodando)
# Ctrl+C nos terminais do backend/frontend
```

### Antes de um Commit

```bash
# Testar tudo em containers
cp backend/.env.docker backend/.env
docker compose down -v  # Limpar tudo
docker compose up -d --build  # Build fresh
# Testar funcionalidades
docker compose down
```

### Deploy/Produção

```bash
# Build de produção
docker compose -f docker-compose.yaml build

# Subir em modo produção
docker compose up -d

# Verificar saúde
docker compose ps
docker compose logs -f
```

---

## Troubleshooting

### Porta já em uso

```bash
# Descobrir o que está usando a porta
lsof -i :5432  # PostgreSQL
lsof -i :8000  # Backend
lsof -i :3000  # Frontend

# Mudar a porta no docker-compose.yaml
ports:
  - "5433:5432"  # Expor 5433 no host
```

### Banco não conecta

```bash
# Verificar se o container está rodando
docker compose ps

# Ver logs do banco
docker compose logs database

# Verificar health check
docker inspect langchain-nextjs-fastapi_database | grep Health

# Reiniciar o banco
docker compose restart database
```

### Frontend não conecta no Backend

```bash
# Verificar variável de ambiente
docker compose exec frontend env | grep API_URL

# Verificar rede Docker
docker network inspect langchain-nextjs-fastapi-template_app-network
```

### Rebuild não funciona

```bash
# Limpar cache do Docker
docker compose down
docker system prune -af
docker compose build --no-cache
docker compose up -d
```

---

## Boas Práticas

1. **Nunca commite arquivos .env** - apenas .env.local e .env.docker como template
2. **Use .env.local para desenvolvimento** - mais rápido e prático
3. **Use .env.docker antes de commits** - testa integração completa
4. **Mantenha volumes nomeados** - evita perda de dados do PostgreSQL
5. **Use health checks** - garante ordem de inicialização correta
6. **Separe redes Docker** - isolamento entre projetos

---

## Próximos Passos

- [ ] Adicionar variáveis sensíveis ao `.env` (não comitar!)
- [ ] Configurar Dockerfile multi-stage para frontend (dev/prod)
- [ ] Adicionar docker-compose.prod.yaml para deploy
- [ ] Configurar volumes para persistência de uploads
- [ ] Adicionar nginx como reverse proxy (produção)
