import dotenv
from pydantic_settings import BaseSettings

from steam_api.common import ROOT

env_file = ROOT / '.env'
if env_file.exists():
    dotenv.load_dotenv(env_file)


class Config(BaseSettings):
    STEAM_API_KEY: str
    STEAM_MY_ID: int


config = Config()
