# Estágio de desenvolvimento
FROM node:20-alpine AS development

WORKDIR /app

# Copiar arquivos de dependências
COPY package*.json ./

# Instalar dependências
RUN npm install

# Copiar o resto do código
COPY . .

# Expor porta do Next.js
EXPOSE 3000

# Comando para desenvolvimento
CMD ["npm", "run", "dev"]


# Estágio de produção
FROM node:20-alpine AS production

WORKDIR /app

# Copiar arquivos de dependências
COPY package*.json ./

# Instalar apenas dependências de produção
RUN npm ci --only=production

# Copiar o resto do código
COPY . .

# Build da aplicação
RUN npm run build

# Expor porta do Next.js
EXPOSE 3000

# Comando para produção
CMD ["npm", "start"]
