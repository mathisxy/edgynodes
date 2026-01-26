from .openai import LLMNodeOpenAI

class LLMNodeMistral(LLMNodeOpenAI):

    def __init__(self, model: str, api_key: str, base_url: str ="https://api.mistral.ai/v1", enable_streaming: bool = False) -> None:
        super().__init__(model=model, api_key=api_key, base_url=base_url, enable_streaming=enable_streaming)