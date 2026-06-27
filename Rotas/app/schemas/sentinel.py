from pydantic import BaseModel


class SentinelInput(BaseModel):
    input: str


class SentinelRequest(BaseModel):
    input: SentinelInput


class SentinelResponse(BaseModel):
    output: str | dict | None = None
