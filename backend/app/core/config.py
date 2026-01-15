from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # =================================================
    # Environment
    # =================================================
    ENV: str = Field(default="dev")

    # =================================================
    # PostgreSQL
    # =================================================
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # =================================================
    # MinIO
    # =================================================
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str
    MINIO_SECURE: bool = False

    # =================================================
    # OpenAI
    # =================================================
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = Field(default="gpt-4.1")

    # =================================================
    # Prompt (Graph Policy)
    # =================================================
    GRAPH_SYSTEM_PROMPT: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()