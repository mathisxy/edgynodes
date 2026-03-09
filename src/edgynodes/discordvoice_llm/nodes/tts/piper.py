import io
import wave
import asyncio
from typing import Tuple

from piper import PiperVoice, SynthesisConfig

from .base import BaseTTSNode
from ...core.states import StateProtocol, SharedProtocol


class PiperTTSNode(BaseTTSNode[StateProtocol, SharedProtocol]):
    """TTS via local Piper model."""

    voice: PiperVoice
    syn_config: SynthesisConfig | None

    def __init__(
        self,
        files: Tuple[str, str] = (
            "piper/de_DE-thorsten_emotional-medium.onnx",
            "piper/de_DE-thorsten_emotional-medium.onnx.json",
        ),
        syn_config: SynthesisConfig | None = None,
        min_stream_chunk_length: int = 20,
    ) -> None:
        super().__init__(min_stream_chunk_length)
        self.voice = PiperVoice.load(files[0], files[1])
        self.syn_config = syn_config

    async def generate_wav_bytes(self, text: str, interrupt: asyncio.Event) -> bytes:
        audio_buffer = io.BytesIO()
        with wave.open(audio_buffer, 'wb') as wav_file:
            self.voice.synthesize_wav(text, wav_file, syn_config=self.syn_config)
        return audio_buffer.getvalue()