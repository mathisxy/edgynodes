from edgynodes.llm.core.nodes import Supports
from .core.nodes import LLMNodeOpenAI

class LLMNodeGemini(LLMNodeOpenAI):


    supports: Supports = Supports(
        remote_image_urls=False
    )

    def __init__(self, model: str, api_key: str, base_url: str ="https://generativelanguage.googleapis.com/v1beta/openai/", enable_streaming: bool = False, extra_body: dict[str, object] | None = None) -> None:
        super().__init__(model=model, api_key=api_key, base_url=base_url,enable_streaming=enable_streaming, extra_body=extra_body)