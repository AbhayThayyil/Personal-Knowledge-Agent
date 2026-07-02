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


settings = Settings()
