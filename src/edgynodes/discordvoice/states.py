import edgygraph
import discord
import asyncio
from pydantic import Field


class StateAttribute(edgygraph.StateAttribute):
    transcriptions: dict[str, str] = Field(default_factory=dict[str, str])


class SharedAttribute(edgygraph.SharedAttribute):

    channel: discord.VoiceChannel

    sink: discord.sinks.Sink | None = None
    client: discord.voice_client.VoiceProtocol | None = None
    text_channel: discord.abc.Messageable | None = None

    recording_finished: asyncio.Event = Field(default_factory=asyncio.Event)


class State(edgygraph.State):

    discordvoice: StateAttribute

class Shared(edgygraph.Shared):

    discordvoice: SharedAttribute