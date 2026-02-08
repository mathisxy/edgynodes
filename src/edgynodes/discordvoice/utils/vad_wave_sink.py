import webrtcvad
import discord
import time
import asyncio
from typing import Literal

class VADWaveSink(discord.sinks.WaveSink):

    FRAME_MS = 20
    SAMPLE_RATE = 48000
    BYTES_PER_SAMPLE = 2

    received_voice: asyncio.Event


    def __init__(self, vad_mode: Literal[0, 1, 2, 3] = 2, dump_initial_silence: bool = True):
        super().__init__()

        self.vad = webrtcvad.Vad(vad_mode)  # 0–3 (3 = aggressiv)
        self.last_voice = time.monotonic()
        self.dump_initial_silence = dump_initial_silence
        
        self.received_voice = asyncio.Event()
        self.frame_size = int(
            self.SAMPLE_RATE * self.FRAME_MS / 1000
        ) * self.BYTES_PER_SAMPLE


    def write(self, data: bytes, user: discord.abc.User):

        for i in range(0, len(data), self.frame_size):
            frame = data[i:i+self.frame_size]
            if len(frame) < self.frame_size:
                continue

            if self.vad.is_speech(frame, self.SAMPLE_RATE):
                self.received_voice.set()
                self.last_voice = time.monotonic()
        
        
        if self.received_voice.is_set():
            
            super().write(data, user)
