from edgygraph import Node
from mistralai import Mistral
import discord

from ..states import StateProtocol, SharedProtocol


from rich import print


class STTMistralNode(Node[StateProtocol, SharedProtocol]):


    model: str
    client: Mistral

    language: str | None

    def __init__(self, api_key: str, model: str = "voxtral-mini-latest", language: str | None = None) -> None:
        self.model = model
        self.client = Mistral(api_key=api_key)
        
        self.language = language


    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:

        async with shared.lock:
            sink = shared.discordvoice.sink
            text_channel = shared.discordvoice.text_channel
            if sink is None:
                raise ValueError("No audio found.")
            if text_channel is None:
                raise ValueError("No text channel found.")
            

        for user_id, audio in sink.audio_data.items():
            if not isinstance(audio, discord.sinks.AudioData):
                raise ValueError("Audio data is not of type AudioData.")

            audio.file.seek(0)  # Wichtig, um den Stream zurückzusetzen
            wav_bytes = audio.file.read()

            # Sende an Mistral-API zur Transkription
            transcription_response = await self.client.audio.transcriptions.complete_async(
                model=self.model,
                file={
                    "content": wav_bytes,
                    "file_name": f"{user_id}.{sink.encoding}",
                },
                language=self.language
            )

            # Ergebnis verarbeiten
            transcription_text = transcription_response.text
            print(f"Transkription für {user_id}: {transcription_text}")

            state.discordvoice.transcriptions[user_id] = transcription_text

            # Optional: Datei für Discord senden (falls gewünscht)
            # wav_file = discord.File(
            #     fp=io.BytesIO(wav_bytes),
            #     filename=f"{user_id}.{sink.encoding}"
            # )
            # await text_channel.send(
            #     content=f"🎤 Audio von <@{user_id}>\n**Transkription:** {transcription_text}",
            #     file=wav_file
            # )


    @classmethod
    def get_audio_duration(cls, wav_bytes: bytes, sample_rate: int = 48000, channels: int = 2, bytes_per_sample: int = 2) -> float:
        """Berechnet die Dauer einer WAV-Datei in Sekunden"""
        audio_data_size = len(wav_bytes) - 44  # 44 Bytes Header
        return audio_data_size / (sample_rate * channels * bytes_per_sample)