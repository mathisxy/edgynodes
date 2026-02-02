from edgygraph import State, Shared, Node
from pydantic import Field
from discord import Message
# from discord import TextChannel, DMChannel, Thread, VoiceChannel, StageChannel, GroupChannel, PartialMessageable
from discord.context_managers import Typing
from discord.ext import commands
from  discord.abc import Messageable

# MessageableChannel = TextChannel | DMChannel | Thread | VoiceChannel | StageChannel | GroupChannel | PartialMessageable

class DiscordTypingManager:

    _active: dict[Messageable, Typing] = {}

    async def start(self, channel: Messageable) -> None:
        if channel in self._active:
            return
        
        typing_ctx: Typing = channel.typing()
        await typing_ctx.__aenter__()
        self._active[channel] = typing_ctx

    async def stop(self, channel: Messageable) -> None:
        if channel not in self._active:
            raise Exception(f"No typing context for channel {channel} found")
        
        typing_ctx: Typing = self._active.pop(channel)
        await typing_ctx.__aexit__(None, None, None)




class DiscordState(State):
    pass

class DiscordShared(Shared):
    discord_message: Message
    discord_bot: commands.Bot
    discord_typing: DiscordTypingManager = Field(default_factory=DiscordTypingManager)



class StartTypingNode(Node[DiscordState, DiscordShared]):

    _channel: Messageable | None

    def __init__(self, channel: Messageable | None = None) -> None:

        self._channel = channel


    async def run(self, state: DiscordState, shared: DiscordShared) -> None:
        
        async with shared.lock:

            channel: Messageable = self._channel or shared.discord_message.channel

            await shared.discord_typing.start(channel)

class StopTypingNode(Node[DiscordState, DiscordShared]):

    _channel: Messageable | None

    def __init__(self, channel: Messageable | None = None) -> None:

        self._channel = channel

    async def run(self, state: DiscordState, shared: DiscordShared) -> None:
        
        async with shared.lock:

            channel: Messageable = self._channel or shared.discord_message.channel

            await shared.discord_typing.stop(channel)