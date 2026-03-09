import discord
from discord.context_managers import Typing

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
