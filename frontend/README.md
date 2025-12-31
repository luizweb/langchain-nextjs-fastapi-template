## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

### Next.js

- Next.js = React + regras + estrutura
- Tudo que está em app/ define páginas, layouts e rotas
- Você não cria rotas manualmente (como no React Router).

### `app/`

Essa pasta usa o App Router (novo padrão do Next.js).
- Pastas = rotas
- page.tsx = página
- layout.tsx = layout compartilhado

### `app/page.tsx``

- Página inicial (/)
- Equivale à rota: http://localhost:3000
- É um componente React

```typescript
export default function Home() {
  return <h1>Olá Next.js</h1>
}
```

### `app/layout.tsx`

Layout global da aplicação. Envolve todas as páginas.

Ideal para:

- Header
- Footer
- Navbar
- Providers (Context, Theme, etc.)

Obrigatório existir no App Router.

### `app/globals.css`

CSS global. 
- Estilos aplicados no projeto inteiro
- Importado automaticamente pelo layout.tsx

Aqui você coloca:
- reset de CSS
- fontes
- estilos base

### `app/favicon.ico`

Ícone da aba do navegador. Next já reconhece automaticamente. Não precisa configurar nada

### `public/`

Arquivos estáticos (imagens, ícones, etc.).  
Tudo aqui fica disponível direto via URL.

public/logo.png --> http://localhost:3000/logo.png

### `package.json`

Coração do projeto. Define:
- Nome do projeto
- Scripts (dev, build, start)
- Dependências (next, react, etc.)

```json
"scripts": {
  "dev": "next dev",
  "build": "next build",
  "start": "next start"
}
```

### `package-lock.json`

Controle de versões exatas das dependências. Gerado automaticamente. Nunca edite manualmente

### `next.config.ts`

Configuração do Next.js

Usado para:
- redirects
- imagens externas
- experimental features
- build settings

### `tsconfig.json`

Configuração do TypeScript

Define:
- regras de tipagem
- paths (@/components)
- nível de rigor

### `eslint.config.mjs`

Configuração de lint (qualidade de código)
- Aponta erros
- Ajuda a manter padrão
- Integrado com Next

### `postcss.config.mjs`

Configuração de CSS avançado

Usado com:
Tailwind, Autoprefixer. Normalmente você não mexe no começo

### `node_modules/`

Dependências instaladas. Nunca edite. Pode apagar e rodar npm install de novo.

### `.next/`

Build do Next.js. Cache. Código compilado. Gerado automaticamente. Pode apagar sem medo (Next recria).

### Componentes reutilizáveis:

Normalmente você cria:
```
components/
  Header.tsx
  Footer.tsx
```

## shadcn

shadcn/ui é uma coleção de componentes React prontos.
https://ui.shadcn.com/ e https://ui.shadcn.com/docs/installation/next


```bash
npx shadcn@latest init
```

### `components.json`


### `lib/utils.ts`

Adicionar componentes:

```bash
npx shadcn@latest add button
```

```typescript
import { Button } from "@/components/ui/button"

export default function Home() {
  return (
    <div>
      <Button>Click me</Button>
    </div>
  )
}
```


### `components/ui`



```
npm install react-icons
```