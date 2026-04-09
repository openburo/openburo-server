from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    twake_url: str = "http://localhost:8080"
    twake_token: str = ""

    model_config = {"env_file": ".env"}


settings = Settings()
