import discord
from typing import Any


class DiscordTemporaryMessageController:

    channel: discord.abc.Messageable
    messages: dict[str, discord.Message]

    def __init__(self, channel: discord.abc.Messageable) -> None:

        self.channel = channel
        self.messages = {}


    async def update(
            self, 
            key: str, 
            content: str | None = None, 
            embeds: discord.Embed | list[discord.Embed] | None = None,
            suppress: bool = False, 
            files: discord.File | list[discord.File] | None = None, 
            delete_after: float | None = None, 
            allowed_mentions: discord.AllowedMentions | None = None, 
            view: discord.ui.View | discord.ui.LayoutView | None = None,
            fail_if_not_exists: bool = False,
            ) -> None:
        
        files = files if isinstance(files, list) else [files] if isinstance(files, discord.File) else None
        embeds = embeds if isinstance(embeds, list) else [embeds] if isinstance(embeds, discord.Embed) else None

        if key in self.messages:
            message = self.messages[key]

            optional_args: dict[str, Any] = {
                'content': content,
                'embeds': embeds,
                'suppress': suppress,
                'attachments': files,
                'delete_after': delete_after,
                'allowed_mentions': allowed_mentions,
                'view': view,
            }
            kwargs = {k: v for k, v in optional_args.items() if v is not None}

            await message.edit(**kwargs)

        else:

            if fail_if_not_exists:
                raise KeyNotFound(f"Message with key {key} does not exist")

            optional_args: dict[str, Any] = {
                'content': content,
                'embeds': embeds,
                'suppress_embeds': suppress,
                'files': files,
                'delete_after': delete_after,
                'allowed_mentions': allowed_mentions,
                'view': view,
            }

            kwargs = {k: v for k, v in optional_args.items() if v is not None}

            message = await self.channel.send(**kwargs)

            self.messages[key] = message

    async def delete(self, key: str) -> None:
        if key in self.messages:
            await self.messages[key].delete()
            del self.messages[key]
        else:
            raise KeyNotFound(f"Message with key {key} does not exist")


class KeyNotFound(Exception):
    pass
