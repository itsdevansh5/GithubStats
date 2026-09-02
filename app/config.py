from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    github_token: str | None = None
    mongo_url: str
    redis_url: str

    model_config = SettingsConfigDict(
                     env_file = ".env"
                     )

settings = Settings()
