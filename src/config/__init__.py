from pydantic_settings import BaseSettings


class WeaviateSettings(BaseSettings):
    url: str = "http://localhost:11480"
    api_key: str = "secr3t"
    collection: str = "DocumentChunks"


class ChunkingSettings(BaseSettings):
    default_chunk_size: int = 1024
    lang: str = "en"
    strategy: str = "wonder"


class Settings(BaseSettings):
    weaviate: WeaviateSettings = WeaviateSettings()
    chunking: ChunkingSettings = ChunkingSettings()


settings = Settings()
