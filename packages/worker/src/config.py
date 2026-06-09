from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LLM_")

    api_key: str
    base_url: str
    model: str
    temperature: float = 0.1


class Settings(BaseSettings):
    llm: LLMSettings = LLMSettings()


settings = Settings()
