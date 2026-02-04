from .core.nodes import LLMNodeOpenAI
from edgynodes.llm.core.nodes import Supports

class LLMNodeOllama(LLMNodeOpenAI):
    """
    LLM Node for Ollama

    Multiple tool calls per response when streaming is enabled are not handled correctly by the ollama api
    """

    supports: Supports = Supports(
        remote_image_urls=False,
    )

    def __init__(self, model: str, api_key: str = "ollama", base_url: str ="http://localhost:11434/v1", enable_streaming: bool = False, keep_alive: str | None = None, extra_body: dict[str, object] | None = None) -> None:
        if keep_alive is not None:
            if extra_body is None:
                extra_body = {}
            extra_body["keep_alive"] = keep_alive
            
        super().__init__(model=model, api_key=api_key, base_url=base_url, enable_streaming=enable_streaming, extra_body=extra_body)