from edgygraph import Node
from llmir import AIChunkText, AIMessage, AIRoles
from mistralai import Mistral
import discord
import io

from ..states import State, Shared


class STTMistralNode(Node[State, Shared]):


    model: str
    client: Mistral

    language: str | None

    def __init__(self, api_key: str, model: str = "voxtral-mini-latest", language: str | None = None) -> None:
        self.model = model
        self.client = Mistral(api_key=api_key)
        
        self.language = language


    async def run(self, state: State, shared: Shared) -> None:

        print("BEFORE SPEECH TO TEXT")
        print(state)

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
            wav_file = discord.File(
                fp=io.BytesIO(wav_bytes),
                filename=f"{user_id}.{sink.encoding}"
            )
            await text_channel.send(
                content=f"🎤 Audio von <@{user_id}>\n**Transkription:** {transcription_text}",
                file=wav_file
            )