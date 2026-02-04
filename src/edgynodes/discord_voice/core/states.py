from edgygraph import State, Shared
import discord


class DiscordVoiceState(State):
    pass

class DiscordVoiceShared(Shared):

    discord_voice_channel: discord.VoiceChannel

    discord_voice_sink: discord.sinks.Sink | None = None
    discord_voice_client: discord.voice_client.VoiceClient | None = None
    discord_voice_text_channel: discord.abc.Messageable | None = None
