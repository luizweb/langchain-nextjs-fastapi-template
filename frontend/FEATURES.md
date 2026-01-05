# 🚀 Seleção de Modelo LLM - Guia de Funcionalidade

## 📋 Visão Geral

Implementamos um sistema completo de seleção de modelos LLM que permite aos usuários escolher qual modelo de inteligência artificial desejam usar no chat, com suporte a múltiplos provedores.

## ✨ Funcionalidades

### 1. **Seleção Dinâmica de Providers**
- ✅ Carregamento automático dos providers disponíveis via API
- ✅ Suporte a Ollama, OpenAI e Serpro
- ✅ Interface visual com badges coloridos por provider

### 2. **Seleção de Modelos**
- ✅ Lista dinâmica de modelos baseada no provider selecionado
- ✅ Display em fonte monoespaçada para melhor legibilidade
- ✅ Contador de modelos disponíveis por provider

### 3. **Persistência de Preferências**
- ✅ Seleção salva automaticamente no localStorage
- ✅ Preferências restauradas ao recarregar a página
- ✅ Feedback visual de salvamento

### 4. **Integração com Chat**
- ✅ Modelo enviado em cada requisição de chat
- ✅ Badge identificador do modelo usado em cada resposta
- ✅ Compatibilidade total com streaming SSE

### 5. **UX Aprimorada**
- ✅ Loading states durante carregamento de providers
- ✅ Error handling com mensagens claras
- ✅ Design responsivo e moderno
- ✅ Ícones intuitivos (Bot, Sparkles)

## 🎨 Interface do Usuário

### Componente LLMSelector

O componente está localizado na sidebar esquerda da página de chat, acima da área de upload de PDFs.

**Elementos visuais:**
```
┌─────────────────────────────────────┐
│ 🤖 Modelo LLM ✨                    │
├─────────────────────────────────────┤
│ Provider                            │
│ ┌─────────────────────────────────┐ │
│ │ [Ollama] (4 modelos)            │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Modelo                              │
│ ┌─────────────────────────────────┐ │
│ │ gpt-oss:120b-cloud              │ │
│ └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│ ✨ Preferências salvas             │
│    automaticamente                  │
└─────────────────────────────────────┘
```

### Cores dos Providers

- **Ollama**: Azul (`blue-500`)
- **OpenAI**: Verde (`green-500`)
- **Serpro**: Roxo (`purple-500`)

### Badge nas Mensagens

Cada resposta do assistente exibe um badge mostrando qual modelo foi usado:

```
┌────────────────────────────────────┐
│ [ollama/gpt-oss:120b-cloud]       │
│                                    │
│ [Resposta do assistente...]       │
└────────────────────────────────────┘
```

## 🔧 Implementação Técnica

### Arquitetura

```
Frontend (React/Next.js)
│
├── components/llm-selector.tsx
│   ├── Fetch providers da API
│   ├── Gerencia estado local
│   ├── Salva no localStorage
│   └── Notifica componente pai
│
└── app/projects/chat/page.tsx
    ├── Recebe seleção via callback
    ├── Envia provider/model na requisição
    └── Exibe badge do modelo usado
```

### Fluxo de Dados

1. **Montagem do Componente**
   ```typescript
   useEffect(() => {
     fetchProviders() → API GET /chat/providers
     ↓
     Carrega preferências do localStorage
     ↓
     Inicializa com default ou preferência salva
     ↓
     onSelectionChange({ provider, model })
   })
   ```

2. **Mudança de Seleção**
   ```typescript
   handleProviderChange(provider)
   ↓
   Auto-seleciona primeiro modelo
   ↓
   Salva no localStorage
   ↓
   onSelectionChange({ provider, model })
   ```

3. **Envio de Mensagem**
   ```typescript
   sendMessage()
   ↓
   POST /chat/stream
   {
     query: "...",
     project_id: 123,
     provider: "ollama",    ← Adicionado
     model: "gpt-oss:..."   ← Adicionado
   }
   ```

## 📦 Estrutura de Dados

### API Response - GET /chat/providers

```typescript
interface LLMProvidersResponse {
  providers: Array<{
    name: string;
    models: string[];
  }>;
  default_provider: string;
  default_model: string;
}

// Exemplo:
{
  "providers": [
    {
      "name": "ollama",
      "models": ["mistral", "llama2", "codellama", "gpt-oss:120b-cloud"]
    },
    {
      "name": "openai",
      "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
    },
    {
      "name": "serpro",
      "models": ["gpt-oss-120b", "deepseek-r1-distill-qwen-14b"]
    }
  ],
  "default_provider": "ollama",
  "default_model": "gpt-oss:120b-cloud"
}
```

### Chat Request - POST /chat/stream

```typescript
interface ChatRequest {
  query: string;
  project_id: number;
  provider: string;  // Novo campo
  model: string;     // Novo campo
}
```

### Message Type

```typescript
interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  toolCalls?: ToolCall[];
  toolResults?: ToolResult[];
  llmProvider?: string;  // Novo campo
  llmModel?: string;     // Novo campo
}
```

## 🎯 Casos de Uso

### Caso 1: Primeiro Acesso
1. Usuário acessa a página de chat
2. LLMSelector carrega providers da API
3. Usa provider/modelo padrão (ollama/gpt-oss:120b-cloud)
4. Salva preferência no localStorage
5. Usuário envia mensagem → usa modelo padrão

### Caso 2: Mudança de Provider
1. Usuário clica no select de Provider
2. Escolhe "OpenAI"
3. Modelo é auto-selecionado para "gpt-4o" (primeiro da lista)
4. Preferência salva automaticamente
5. Próxima mensagem usa OpenAI/gpt-4o

### Caso 3: Retorno à Página
1. Usuário retorna ao chat depois
2. LLMSelector restaura preferências do localStorage
3. Mantém OpenAI/gpt-4o selecionado
4. Continua conversação com mesmo modelo

### Caso 4: Modelo Específico
1. Usuário quer testar gpt-3.5-turbo
2. Seleciona OpenAI como provider
3. Seleciona gpt-3.5-turbo no dropdown de modelos
4. Envia mensagem de teste
5. Badge na resposta confirma: "openai/gpt-3.5-turbo"

## 💡 Benefícios para UX

1. **Transparência**: Usuário sempre sabe qual modelo está sendo usado
2. **Controle**: Poder de escolha entre diferentes modelos
3. **Conveniência**: Preferências salvas automaticamente
4. **Feedback**: Visual claro do modelo em cada resposta
5. **Flexibilidade**: Fácil troca entre modelos durante a conversa

## 🔒 Segurança

- ✅ Token JWT validado em todas as requisições
- ✅ Preferências salvas apenas localmente (não no servidor)
- ✅ Validação de provider/modelo no backend
- ✅ Error handling para providers inválidos

## 📱 Responsividade

O componente é totalmente responsivo e se adapta a diferentes tamanhos de tela:

- **Desktop**: Sidebar fixa de 288px (w-72)
- **Tablet**: Layout ajustado com scroll
- **Mobile**: Componente mantém usabilidade

## 🚀 Performance

- ⚡ Carregamento único na montagem do componente
- ⚡ Cache de providers no estado local
- ⚡ localStorage para evitar requests repetidas
- ⚡ Lazy loading do componente via dynamic import (possível)

## 🧪 Testando a Funcionalidade

### Teste Manual

1. **Acesse a página de chat:**
   ```
   http://localhost:3000/projects/chat?id=1
   ```

2. **Verifique o seletor na sidebar:**
   - Deve exibir providers disponíveis
   - Badge colorido para cada provider
   - Contador de modelos

3. **Troque o provider:**
   - Selecione OpenAI
   - Observe mudança automática do modelo
   - Mensagem de confirmação

4. **Envie uma mensagem:**
   - Digite qualquer pergunta
   - Observe badge na resposta: "openai/gpt-4o"

5. **Recarregue a página:**
   - Seleção deve ser mantida
   - Mesmo provider/modelo selecionado

### Teste de API

```bash
# 1. Listar providers disponíveis
curl http://localhost:8000/chat/providers \
  -H "Authorization: Bearer YOUR_TOKEN"

# 2. Enviar mensagem com modelo específico
curl -X POST http://localhost:8000/chat/stream \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Olá!",
    "project_id": 1,
    "provider": "openai",
    "model": "gpt-4o"
  }'
```

## 📝 Próximas Melhorias (Sugestões)

1. **Favoritos**: Marcar modelos favoritos
2. **Histórico**: Mostrar últimos modelos usados
3. **Comparação**: Chat side-by-side com modelos diferentes
4. **Métricas**: Exibir tempo de resposta por modelo
5. **Custos**: Mostrar estimativa de custo (OpenAI)
6. **Compartilhamento**: Compartilhar chat com modelo específico
7. **Templates**: Criar presets de modelo por tipo de tarefa

## 🎓 Aprendizados

Esta implementação demonstra:

- ✅ Integração completa frontend-backend
- ✅ Gerenciamento de estado em React
- ✅ Persistência local com localStorage
- ✅ Design system com shadcn/ui
- ✅ TypeScript para type-safety
- ✅ UX patterns para seleções dinâmicas
- ✅ Error handling robusto
- ✅ Feedback visual contínuo

---

**Desenvolvido com ❤️ usando Next.js 16, React 19 e shadcn/ui**
