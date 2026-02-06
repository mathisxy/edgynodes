import edgygraph
from discord.ext import commands
from discord.context_managers import Typing
import discord
from pydantic import Field


class DiscordTypingManager:

    _active: dict[discord.abc.Messageable, Typing] = {}

    async def start(self, channel: discord.abc.Messageable) -> None:
        if channel in self._active:
            return
        
        typing_ctx: Typing = channel.typing()
        await typing_ctx.__aenter__()
        self._active[channel] = typing_ctx

    async def stop(self, channel: discord.abc.Messageable) -> None:
        if channel not in self._active:
            raise Exception(f"No typing context for channel {channel} found")
        
        typing_ctx: Typing = self._active.pop(channel)
        await typing_ctx.__aexit__(None, None, None)



class State(edgygraph.State):
    pass

class Shared(edgygraph.Shared):    

    discord_text_channel: discord.abc.Messageable

    discord_bot: commands.Bot
    discord_typing: DiscordTypingManager = Field(default_factory=DiscordTypingManager)