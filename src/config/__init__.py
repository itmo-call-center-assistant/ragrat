from pydantic_settings import BaseSettings, SettingsConfigDict


class WeaviateSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="WEAVIATE_")

    url: str
    api_key: str
    collection: str = "DocumentChunks"


class ChunkingSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CHUNKING_")

    default_chunk_size: int = 1024
    lang: str = "en"
    strategy: str = "wonder"


class EmbeddingSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EMBEDDING_")

    model: str = "deepvk/USER2-base"
    pooling: str = "mean"


class Settings(BaseSettings):
    weaviate: WeaviateSettings = WeaviateSettings()
    chunking: ChunkingSettings = ChunkingSettings()
    embedding: EmbeddingSettings = EmbeddingSettings()


settings = Settings()
