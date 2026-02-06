import edgygraph
import discord


class State(edgygraph.State):
    pass

class Shared(edgygraph.Shared):

    discord_voice_channel: discord.VoiceChannel

    discord_voice_sink: discord.sinks.Sink | None = None
    discord_voice_client: discord.voice_client.VoiceClient | None = None