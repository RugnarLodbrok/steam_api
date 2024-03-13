from pydantic import BaseModel


class TestDatum(BaseModel):
    name: str
    arg: str | None = None
