import asyncio
import logging
import time

from edgygraph.nodes import Node
from edgygraph.states import SharedProtocol, StateProtocol

import pynvml

class CheckFreeVRAMNode(Node[StateProtocol, SharedProtocol]):

    dependencies = {"pynvml"}

    def __init__(self, required_gb: float = 8, timeout: float = 20, interval: float = 1):
        self.required_gb = required_gb
        self.timeout = timeout
        self.interval = interval

    @classmethod
    def check_free_vram(cls, required_gb: float) -> None:
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)  # Nur GPU 0
        info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        free_gb = info.free / 1024**3
        if free_gb < required_gb:
            raise RuntimeError(f"Not enough VRAM: {free_gb:.2f} GB free, {required_gb} GB required")
        logging.info(f"Enough VRAM: {free_gb:.2f} GB free, {required_gb} GB required")

    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:
        logging.info("Waiting for VRAM")
        
        start = time.time()

        while True:
            try:
                self.check_free_vram(required_gb=self.required_gb)
                break
            except RuntimeError as e:
                if (time.time() - start) >= self.timeout:
                    logging.exception(f"Wait for vram timeout: {self.timeout}s, interval: {self.interval}")
                    raise TimeoutError(f"Timeout: {e}")
                else:
                    await asyncio.sleep(self.interval)
