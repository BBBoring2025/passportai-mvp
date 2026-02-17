from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/passportai"
    cors_origins: str = "http://localhost:3000"
    app_env: str = "development"
    log_level: str = "info"

    # JWT auth
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    # File storage
    upload_dir: str = "./uploads"

    # Optional; required in later sprints
    supabase_url: str = ""
    supabase_service_key: str = ""
    anthropic_api_key: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
