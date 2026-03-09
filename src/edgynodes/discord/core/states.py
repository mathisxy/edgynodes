import edgygraph
from discord.ext import commands
import discord
from pydantic import Field
from typing import Protocol, runtime_checkable

from .utils.typing_manager import DiscordTypingManager


class StateAttribute(edgygraph.StateAttribute):
    pass

class SharedAttribute(edgygraph.SharedAttribute):    

    text_channel: discord.abc.Messageable

    bot: commands.Bot
    typing: DiscordTypingManager = Field(default_factory=DiscordTypingManager)


@runtime_checkable
class StateProtocol(edgygraph.StateProtocol, Protocol):

    discord: StateAttribute

@runtime_checkable
class SharedProtocol(edgygraph.SharedProtocol, Protocol):

    discord: SharedAttribute