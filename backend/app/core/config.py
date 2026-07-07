from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Personal Knowledge Agent"
    database_url: str = "sqlite:///./pka.db"
    secret_key: str = "dev-secret-change-me"
    access_token_expire_minutes: int = 60 * 24
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 50
    cors_origins: list[str] = ["http://localhost:5173"]

    ollama_base_url: str = "http://localhost:11434"
    embedding_model: str = "nomic-embed-text"
    chat_model: str = "qwen3:8b"
    chroma_dir: str = "./chroma"
    chunk_size: int = 500
    chunk_overlap: int = 50
    chat_top_k: int = 5
    agent_temperature: float = 0.0
    agent_max_tool_rounds: int = 5


settings = Settings()
