import edgygraph
from queue import Queue
from typing import Protocol, runtime_checkable
from pydantic import Field


class StateAttribute(edgygraph.StateAttribute):
    requested_keys: Queue[str] = Queue()
    results: dict[str, str] = Field(default_factory=dict)

class SharedAttribute(edgygraph.SharedAttribute):    
    pass


@runtime_checkable
class StateProtocol(edgygraph.StateProtocol, Protocol):

    redis: StateAttribute

@runtime_checkable
class SharedProtocol(edgygraph.SharedProtocol, Protocol):

    redis: SharedAttribute