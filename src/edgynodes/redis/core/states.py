import edgygraph as e
from typing import Protocol, runtime_checkable
from pydantic import Field
from redis.asyncio import Redis

class StateAttribute(e.StateAttribute):
    read: list[str] = Field(default_factory=list)
    write: list[dict[str, str]] = Field(default_factory=list[dict[str, str]])
    results: dict[str, str] = Field(default_factory=dict)

class SharedAttribute(e.SharedAttribute):    
    connection: Redis = Field(default_factory=lambda: Redis(decode_responses=True))


@runtime_checkable
class StateProtocol(e.StateProtocol, Protocol):

    redis: StateAttribute

@runtime_checkable
class SharedProtocol(e.SharedProtocol, Protocol):

    redis: SharedAttribute