from edgygraph import State, Shared
from discord import Message
from discord.ext import commands
from discord.abc import Messageable
from discord.context_managers import Typing
from pydantic import Field


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



class DiscordTextState(State):
    pass

class DiscordTextShared(Shared):
    discord_message: Message
    discord_bot: commands.Bot
    discord_typing: DiscordTypingManager = Field(default_factory=DiscordTypingManager)