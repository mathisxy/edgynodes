from .openai import LLMNodeOpenAI

class LLMNodeClaude(LLMNodeOpenAI):

    def __init__(self, model: str, api_key: str, base_url: str = "https://api.anthropic.com/v1/", enable_streaming: bool = False, extra_body: dict[str, object] | None = None) -> None:
        super().__init__(model=model, api_key=api_key, base_url=base_url, enable_streaming=enable_streaming, extra_body=extra_body)