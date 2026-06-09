from pydantic_settings import BaseSettings, SettingsConfigDict


class QdrantSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="QDRANT_")

    url: str
    collection: str = "DocumentChunks"


class EmbeddingSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EMBEDDING_")

    model: str = "deepvk/USER2-base"


class Settings(BaseSettings):
    qdrant: QdrantSettings = QdrantSettings()
    embedding: EmbeddingSettings = EmbeddingSettings()


settings = Settings()
