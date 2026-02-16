import edgygraph
import discord
from typing import Protocol, runtime_checkable


class StateAttribute(edgygraph.StateAttribute):
    pass

class SharedAttribute(edgygraph.SharedAttribute):
    message: discord.Message


@runtime_checkable
class StateProtocol(edgygraph.StateProtocol, Protocol):

    discordmessage: StateAttribute

@runtime_checkable
class SharedProtocol(edgygraph.SharedProtocol, Protocol):

    discordmessage: SharedAttribute