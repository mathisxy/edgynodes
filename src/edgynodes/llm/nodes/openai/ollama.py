from .openai import LLMOpenAINode
from ...core.supports import Supports


class LLMOllamaNode(LLMOpenAINode):
    """
    LLM Node for Ollama.

    *Note*: Multiple tool calls per response when streaming is enabled are not handled correctly by the Ollama API.

    Args:
        model: The model to use.
        api_key: The API key is ommited with the value "ollama".
        base_url: The base URL to use, defaulting to the standard local Ollama API URL.
        enable_streaming: Whether to enable streaming.
    """

    supports: Supports = Supports(
        remote_image_urls=False,
    )

    def __init__(self, model: str, api_key: str = "ollama", base_url: str ="http://localhost:11434/v1", stream: bool = False, extra_body: dict[str, object] | None = None) -> None:
        super().__init__(model=model, api_key=api_key, base_url=base_url, stream=stream, extra_body=extra_body)