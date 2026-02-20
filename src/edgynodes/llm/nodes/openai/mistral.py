from .openai import LLMOpenAINode

class LLMMistralNode(LLMOpenAINode):

    def __init__(self, model: str, api_key: str, base_url: str ="https://api.mistral.ai/v1", stream: bool = False, extra_body: dict[str, object] | None = None) -> None:
        super().__init__(model=model, api_key=api_key, base_url=base_url, enable_streaming=stream, extra_body=extra_body)