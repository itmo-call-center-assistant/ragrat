from pydantic_settings import BaseSettings, SettingsConfigDict


class WeaviateSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="WEAVIATE_")

    url: str
    api_key: str
    collection: str = "DocumentChunks"


class ChunkingSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CHUNKING_")

    default_chunk_size: int = 1024


class EmbeddingSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EMBEDDING_")

    model: str = "deepvk/USER2-base"
    pooling: str = "mean"


class OpenAISettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OPENAI_")

    api_key: str
    base_url: str
    model: str


class Settings(BaseSettings):
    weaviate: WeaviateSettings = WeaviateSettings()
    chunking: ChunkingSettings = ChunkingSettings()
    embedding: EmbeddingSettings = EmbeddingSettings()
    openai: OpenAISettings = OpenAISettings()


settings = Settings()
