from pydantic import BaseSettings


class Config(BaseSettings):
    STEAM_API_KEY: str
    STEAM_MY_ID: int


config = Config()
