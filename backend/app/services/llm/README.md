# LLM Provider System

Sistema modular para gerenciar múltiplos provedores de LLM (Large Language Models) no projeto.

## 📁 Estrutura

```
app/services/llm/
├── __init__.py              # Module exports
├── README.md                # This file
├── base.py                  # Abstract base class for providers
├── llm_factory.py           # Factory for creating LLM instances
├── ollama_provider.py       # Ollama provider implementation
├── openai_provider.py       # OpenAI provider implementation
└── serpro_provider.py       # Serpro provider implementation
```

## 🎯 Arquitetura

### Padrão de Projeto

O sistema utiliza o **Factory Pattern** combinado com **Strategy Pattern**:

1. **LLMProvider (base.py)**: Interface abstrata que todos os providers implementam
2. **Providers concretos**: Implementações específicas para cada serviço (Ollama, OpenAI, Serpro)
3. **LLMFactory**: Factory class que gerencia a criação e seleção de providers

### Diagrama

```
┌─────────────────┐
│  LLMFactory     │
│  - providers    │◄─────────┐
│  + get_model()  │          │
└─────────────────┘          │
         │                   │
         │ uses              │
         ▼                   │
┌─────────────────┐          │
│  LLMProvider    │          │
│  (Abstract)     │          │
│  + get_model()  │          │
│  + get_models() │          │
└─────────────────┘          │
         △                   │
         │                   │
    implements               │
         │                   │
    ┌────┴────┬──────────────┴───────┐
    │         │                      │
┌───┴────┐ ┌──┴─────┐ ┌─────────────┴──┐
│ Ollama │ │ OpenAI │ │ Serpro         │
│Provider│ │Provider│ │ Provider       │
└────────┘ └────────┘ └────────────────┘
```

## 🚀 Uso

### 1. Listar Providers Disponíveis

```python
from app.services.llm import LLMFactory

factory = LLMFactory()
providers = factory.list_providers()
# Output: ['ollama', 'openai', 'serpro']
```

### 2. Listar Modelos de um Provider

```python
models = factory.list_models('ollama')
# Output: ['mistral', 'llama2', 'codellama', 'gpt-oss:120b-cloud']
```

### 3. Criar Instância de Modelo

```python
# Get model instance
llm = factory.get_model(
    provider_name='ollama',
    model_name='mistral',
    temperature=0.7  # Optional parameters
)

# Use the model
response = llm.invoke("Hello, how are you?")
```

### 4. Usar no RAG Agent

```python
from app.services.llm import LLMFactory
from app.agents.rag import create_rag_agent

# Create LLM instance
factory = LLMFactory()
llm = factory.get_model('openai', 'gpt-4o')

# Create RAG agent with the selected LLM
agent = create_rag_agent(llm)

# Use the agent
result = await agent.ainvoke({
    "messages": [{"role": "user", "content": "What is AI?"}]
})
```

## 🔧 Configuração

### Variáveis de Ambiente

Configure as credenciais no arquivo `.env`:

```bash
# Ollama
OLLAMA_BASE_URL=http://localhost:11434

# OpenAI
OPENAI_API_KEY=sk-...

# Serpro
SERPRO_USERNAME=your-username
SERPRO_PASSWORD=your-password
SERPRO_TOKEN_URL=https://api.serpro.gov.br/oauth2/token
SERPRO_API_BASE_URL=https://api.serpro.gov.br/gateway/v1

# Default Configuration
DEFAULT_LLM_PROVIDER=ollama
DEFAULT_LLM_MODEL=gpt-oss:120b-cloud
```

### Settings (app/settings.py)

As configurações são carregadas automaticamente pela classe `Settings`:

```python
from app.settings import Settings

settings = Settings()
print(settings.DEFAULT_LLM_PROVIDER)  # 'ollama'
print(settings.DEFAULT_LLM_MODEL)     # 'gpt-oss:120b-cloud'
```

## 📡 API Endpoints

### GET /chat/providers

Lista todos os providers e modelos disponíveis:

```bash
curl http://localhost:8000/chat/providers
```

Resposta:
```json
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

### POST /chat/stream

Enviar mensagem com seleção de modelo:

```bash
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "What is AI?",
    "project_id": 1,
    "provider": "openai",
    "model": "gpt-4o"
  }'
```

## 🔌 Adicionar Novo Provider

Para adicionar um novo provider:

### 1. Criar Provider Class

```python
# app/services/llm/custom_provider.py
from typing import List
from langchain_core.runnables import Runnable
from app.services.llm.base import LLMProvider
from app.settings import Settings

class CustomProvider(LLMProvider):
    """Provider for Custom LLM service."""

    def __init__(self):
        """Initialize with settings."""
        settings = Settings()
        self.api_key = settings.CUSTOM_API_KEY
        self.base_url = settings.CUSTOM_BASE_URL

    def get_model(self, model_name: str, **kwargs) -> Runnable:
        """Return a Custom LLM instance."""
        # Import custom LLM class
        from langchain_community.llms import CustomLLM

        params = {'api_key': self.api_key}
        params.update(kwargs)
        return CustomLLM(model=model_name, **params)

    def get_available_models(self) -> List[str]:
        """Return available models."""
        return ['model-1', 'model-2']
```

### 2. Registrar no Factory

```python
# app/services/llm/llm_factory.py
from app.services.llm.custom_provider import CustomProvider

class LLMFactory:
    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {
            'ollama': OllamaProvider(),
            'openai': OpenAIProvider(),
            'serpro': SerproProvider(),
            'custom': CustomProvider(),  # Add here
        }
```

### 3. Adicionar Settings

```python
# app/settings.py
class Settings(BaseSettings):
    # ... existing settings ...

    # Custom Provider
    CUSTOM_API_KEY: str = ''
    CUSTOM_BASE_URL: str = 'https://api.custom.com'
```

### 4. Atualizar .env.example

```bash
# Custom Provider
CUSTOM_API_KEY=
CUSTOM_BASE_URL=https://api.custom.com
```

## 🧪 Testes

```python
# Test provider instantiation
from app.services.llm import LLMFactory

factory = LLMFactory()

# Test each provider
for provider_name in factory.list_providers():
    print(f"\nProvider: {provider_name}")
    models = factory.list_models(provider_name)
    print(f"Models: {models}")

    # Test model creation
    llm = factory.get_model(provider_name, models[0])
    print(f"Model created: {type(llm)}")
```

## 📝 Boas Práticas

1. **Sempre use a Factory**: Não instancie providers diretamente
2. **Configuração no .env**: Nunca hardcode credenciais
3. **Type hints**: Use `Runnable` do LangChain Core
4. **Error handling**: Valide se o provider existe antes de usar
5. **Documentação**: Documente novos providers no README

## 🔍 Troubleshooting

### Provider não encontrado
```python
llm = factory.get_model('invalid', 'model')
# Returns None - sempre valide!

if llm is None:
    raise HTTPException(status_code=400, detail="Provider not found")
```

### Credenciais inválidas
- Verifique o arquivo `.env`
- Confirme que as variáveis estão carregadas em `Settings`
- Teste conexão com o provider manualmente

### Modelo não suportado
- Liste modelos disponíveis com `factory.list_models(provider_name)`
- Verifique documentação do provider
