import edgygraph
import discord
import asyncio
from pydantic import Field
from typing import Protocol, runtime_checkable


class StateAttribute(edgygraph.StateAttribute):
    transcriptions: dict[int, str] = Field(default_factory=dict[int, str])


class SharedAttribute(edgygraph.SharedAttribute):

    channel: discord.VoiceChannel

    sink: discord.sinks.Sink | None = None
    client: discord.voice_client.VoiceClient | None = None
    text_channel: discord.abc.Messageable | None = None

    recording_finished: asyncio.Event = Field(default_factory=asyncio.Event)


@runtime_checkable
class StateProtocol(edgygraph.StateProtocol, Protocol):

    discordvoice: StateAttribute

@runtime_checkable
class SharedProtocol(edgygraph.SharedProtocol, Protocol):

    discordvoice: SharedAttribute