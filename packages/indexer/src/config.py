from pydantic_settings import BaseSettings, SettingsConfigDict


class ChunkingSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CHUNKING_")

    default_chunk_size: int = 1024


class Settings(BaseSettings):
    chunking: ChunkingSettings = ChunkingSettings()


settings = Settings()
