from .openai import LLMOpenAINode

class LLMClaudeNode(LLMOpenAINode):

    def __init__(self, model: str, api_key: str, base_url: str = "https://api.anthropic.com/v1/", stream: bool = False, extra_body: dict[str, object] | None = None) -> None:
        super().__init__(model=model, api_key=api_key, base_url=base_url, stream=stream, extra_body=extra_body)