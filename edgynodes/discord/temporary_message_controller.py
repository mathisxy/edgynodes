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
            content: str, 
            embeds: discord.Embed | list[discord.Embed] | None = None,
            suppress: bool = False, 
            files: discord.File | list[discord.File] | None = None, 
            delete_after: float | None = None, 
            allowed_mentions: discord.AllowedMentions | None = None, 
            view: discord.ui.View | discord.ui.LayoutView | None = None,
            fail_if_not_exists: bool = False,
            ) -> None:
        
        files = files if isinstance(files, list) else [files] if isinstance(files, discord.File) else []
        embeds = embeds if isinstance(embeds, list) else [embeds] if isinstance(embeds, discord.Embed) else []

        if key in self.messages:
            message = self.messages[key]

            await message.edit(
                content=content,
                embeds=embeds,
                suppress=suppress,
                attachments=files,
                delete_after=delete_after,
                allowed_mentions=allowed_mentions,
                view=view,
            )

        else:

            if fail_if_not_exists:
                raise KeyNotFound(f"Message with key {key} does not exist")

            optional_args: dict[str, Any] = {
                'delete_after': delete_after,
                'allowed_mentions': allowed_mentions,
                'view': view,
            }

            kwargs = {k: v for k, v in optional_args.items() if v is not None}

            message = await self.channel.send(
                content=content,
                embeds=embeds,
                suppress_embeds=suppress,
                files=files,
                **kwargs,
            )

            self.messages[key] = message

    async def delete(self, key: str) -> None:
        if key in self.messages:
            await self.messages[key].delete()
            del self.messages[key]
        else:
            raise KeyNotFound(f"Message with key {key} does not exist")


class KeyNotFound(Exception):
    pass

# class DiscordProgressController:
#     def __init__(
#         self,
#         message: discord.TextChannel | discord.Thread | discord.DMChannel,
#         title: str = "Progress",
#         length: int = 20
#     ):
#         self.message = message
#         self.title = title
#         self.length = length

#     def _progress_bar(self, progress: float) -> str:
#         progress = max(0.0, min(1.0, progress))
#         filled = int(self.length * progress)
#         empty = self.length - filled
#         percent = int(progress * 100)
#         return f"[{'█' * filled}{'░' * empty}] {percent}%"

#     async def update(
#         self,
#         progress: float,
#         text: str = "",
#         thumbnail_url: str | None = None
#     ):
#         embed = discord.Embed(title=self.title, color=0x5865F2)
#         embed.description = self._progress_bar(progress)

#         if text:
#             embed.add_field(name="Status", value=text, inline=False)

#         if thumbnail_url:
#             embed.set_thumbnail(url=thumbnail_url)

#         await self.message.edit(embed=embed)
