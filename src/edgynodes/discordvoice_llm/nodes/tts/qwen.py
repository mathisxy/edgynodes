import asyncio
import io
import soundfile as sf # type: ignore
import torch

from qwen_tts import Qwen3TTSModel  # type: ignore

from .base import BaseTTSNode
from ...core.states import StateProtocol, SharedProtocol


class Qwen3TTSNode(BaseTTSNode[StateProtocol, SharedProtocol]):
    """
    TTS via Qwen3-TTS (VoiceDesign / CustomVoice).

    The `instruct` is a natural language prompt used by VoiceDesign,
    e.g. "A warm, male German voice speaking calmly".
    For CustomVoice, pass the appropriate `speaker` parameter instead.
    """

    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
        language: str = "German",
        speaker: str = "Ryan",
        instruct: str = "A calm, natural German male voice",
        device_map: str = "cuda:0",
        min_stream_chunk_length: int = 20,
    ) -> None:
        super().__init__(min_stream_chunk_length)
        self.tts_model = Qwen3TTSModel.from_pretrained( # type: ignore
            model_name, 
            device_map=device_map,
            dtype = torch.bfloat16
        )
        self.voice_instruct = instruct
        self.speaker = speaker
        self.language = language

    async def generate_wav_bytes(self, text: str, interrupt: asyncio.Event) -> bytes:
        # qwen-tts inference is synchronous/blocking → run in threadpool
        loop = asyncio.get_event_loop()
        wav_bytes = await loop.run_in_executor(None, self._generate_voice, text)
        return wav_bytes

    def _generate_voice(self, text: str) -> bytes:
        print(self.tts_model.get_supported_speakers())

        if self.tts_model.get_supported_speakers():
            result = self.tts_model.generate_custom_voice( # type: ignore
                text,
                speaker=self.speaker,
                language=self.language,
                instruct=self.voice_instruct,
            )

        else:
            result = self.tts_model.generate_voice_design( # type: ignore
                text,
                instruct=self.voice_instruct,
                language=self.language,
            )

        audio_list, sample_rate = result
        audio = audio_list[0]

        buf = io.BytesIO()
        sf.write(buf, audio, sample_rate, format="WAV", subtype="PCM_16") # type: ignore
        buf.seek(0)
        return buf.read()