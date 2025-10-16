from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = Field(default="dev")

    DATABASE_URL: str
    RABBITMQ_URL: str

    FAISS_INDEX_PATH: str = Field(default="./data/index.faiss")
    INDEX_LOCK_PATH: str = Field(default="./data/index.lock")

    EMBEDDING_MODEL_NAME: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")

    CHUNK_TOKENS: int = Field(default=800)
    CHUNK_OVERLAP: int = Field(default=100)

    USE_LLM: int = Field(default=0)  # 0 or 1
    LLM_API_KEY: str | None = None
    LLM_MODEL: str = Field(default="gemini-2.5-flash")

settings = Settings()  # singleton