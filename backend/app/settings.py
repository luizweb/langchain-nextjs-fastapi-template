from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8', extra='ignore'
    )

    # Database
    DATABASE_URL: str

    # JWT Authentication
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # LLM Providers
    # Ollama
    OLLAMA_BASE_URL: str = 'http://10.68.100.40:8000/'

    # OpenAI
    OPENAI_API_KEY: str = ''

    # Serpro
    SERPRO_USERNAME: str = 'SgBIvMn20FNNhY5S7DlVfF72TOwa'
    SERPRO_PASSWORD: str = 'FDi5SCpz9iVZ6yd33NVm2SC2SCAa'
    SERPRO_TOKEN_URL: str = (
        'https://e-api-serprollm.ni.estaleiro.serpro.gov.br/oauth2/token'
    )
    SERPRO_API_BASE_URL: str = (
        'https://e-api-serprollm.ni.estaleiro.serpro.gov.br/gateway/v1'
    )

    # Default LLM Configuration
    DEFAULT_LLM_PROVIDER: str = 'ollama'
    DEFAULT_LLM_MODEL: str = 'gpt-oss:120b-cloud'
