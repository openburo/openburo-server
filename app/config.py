from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    cozy_url: str = "http://localhost:8080"
    cozy_token: str = ""

    model_config = {"env_file": ".env"}


settings = Settings()
