import edgygraph
from typing import Protocol, runtime_checkable

from .utils.message_controller import TemporaryMessageController


class StateAttribute(edgygraph.StateAttribute):
    pass

class SharedAttribute(edgygraph.SharedAttribute):
    controller: TemporaryMessageController


@runtime_checkable
class StateProtocol(edgygraph.StateProtocol, Protocol):
    discordtmp: StateAttribute

@runtime_checkable
class SharedProtocol(edgygraph.SharedProtocol, Protocol):
    discordtmp: SharedAttribute