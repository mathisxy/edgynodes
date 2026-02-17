from edgygraph import Node
import discord
from llmir import AIRoles, AIChunkText, AIMessage, AIChunks
import io
from piper import PiperVoice, SynthesisConfig
from typing import Tuple
import wave

from ..states import StateProtocol, SharedProtocol


class PiperTTSNode(Node[StateProtocol, SharedProtocol]):

    voice: PiperVoice
    syn_config: SynthesisConfig | None


    def __init__(self, files: Tuple[str, str] = ("piper/de_DE-thorsten_emotional-medium.onnx", "piper/de_DE-thorsten_emotional-medium.onnx.json"), syn_config: SynthesisConfig | None = None) -> None:

        self.voice = PiperVoice.load(files[0], files[1])
        self.syn_config = syn_config


    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:

        async with shared.lock:

            voice_client = shared.discordvoice.client
            stream = shared.llm.stream

        if voice_client is None:
            raise ValueError("No voice client found.")
        
        print("PIPER TTS")

        print(state.llm.new_messages)

        current_text = ""
        
        for message in state.llm.new_messages:

            print(message)

            if message.role == AIRoles.MODEL:

                for text in [chunk.text for chunk in message.chunks if isinstance(chunk, AIChunkText)]:

                    if text.strip() == "":
                        continue
                    
                    current_text += text


        if current_text:
            await self.tts(current_text, voice_client)


        if stream is not None:

            chunks: list[AIChunks] = []
            current_text = ""

            async with stream:

                async for chunk in stream:

                    if isinstance(chunk, AIChunkText):
                        current_text += chunk.text

                        complete, remaining = self.extract_complete_lines(current_text, min_chars=60)

                        current_text = remaining

                        if complete:
                            print(f"COMPLETE: {complete}")
                            await self.tts(complete, voice_client)
                            chunks.append(AIChunkText(text=complete))

                    else:
                        chunks.append(chunk)


                if current_text:
                    await self.tts(current_text, voice_client)
                chunks.append(AIChunkText(text=current_text))
            

            if chunks:
                state.llm.new_messages.append(AIMessage(role=AIRoles.MODEL, chunks=chunks))

            print(state.llm.new_messages)

            async with shared.lock:
                shared.llm.stream = None


    async def tts(self, text: str, voice_client: discord.VoiceClient) -> None:

        print(self.voice)
        print("TEXT:")
        print(text)


        if not text:
            raise ValueError("Text is empty")

        audio_buffer = io.BytesIO()
        with wave.open(audio_buffer, 'wb') as wav_file:
            self.voice.synthesize_wav(text, wav_file)

        # # TTS generieren - Audio-Chunks sammeln
        # audio_data = b''
        # for audio_chunk in self.voice.synthesize(text, syn_config=self.syn_config):
        #     audio_data += audio_chunk.audio_int16_bytes
        
        # # WAV-Datei im Speicher erstellen
        # audio_bytes = io.BytesIO()
        # with wave.open(audio_bytes, 'wb') as wav_file:
        #     wav_file.setnchannels(1)  # Mono
        #     wav_file.setsampwidth(2)  # 16-bit
        #     wav_file.setframerate(self.voice.config.sample_rate)
        #     wav_file.writeframes(audio_data)
        
        audio_buffer.seek(0)
        
        # Play Audio
        audio_source = discord.FFmpegPCMAudio(
            audio_buffer,
            pipe=True,
            before_options='-f wav',
            options='-af afade=t=in:st=0:d=0.01', # To suppress clicking noise at the beginning
        )
        
        await voice_client.play(audio_source, wait_finish=True) # type: ignore

        


    @classmethod
    def extract_complete_lines(cls, text: str, min_chars: int = 10):

        last_newline = text.rfind('\n')
        
        if last_newline == -1:
            return None, text
        
        if last_newline >= min_chars:
            complete = text[:last_newline]
            remaining = text[last_newline + 1:]
            return complete, remaining
        
        return None, text


            