import re
from edgygraph import Node
from llmir import AIChunks, AIChunkText

from ...states import StateProtocol, SharedProtocol
from .utils.streams import TransformStream



class StripFormattingsNode(Node[StateProtocol, SharedProtocol]):

    
    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:
        
        for message in state.llm.messages:
            for chunk in message.chunks:
                if isinstance(chunk, AIChunkText):
                    chunk.text = self.strip_symbols(chunk.text)


        async with shared.lock:

            if shared.llm.stream:

                shared.llm.stream = TransformStream(shared.llm.stream, self.strip_chunk)


    @classmethod
    def strip_chunk(cls, chunk: AIChunks) -> AIChunks:
        if isinstance(chunk, AIChunkText):
            chunk.text = cls.strip_symbols(chunk.text)
            chunk.text = cls.strip_markdown(chunk.text)
        return chunk


    @classmethod
    def strip_symbols(cls, text: str) -> str:
        """
        Strip symbols like emojis, special characters, and other non-text elements from the text.

        Args:
            text (str): The input text to be cleaned.

        Returns:
            str: The cleaned text with symbols removed.
        """

        text = re.sub(r'[\U00010000-\U0010ffff]', '', text)  # Surrogate pairs (most emojis)
        text = re.sub(r'[\U00002600-\U000027BF]', '', text)  # Misc symbols
        text = re.sub(r'[\U0001F000-\U0001FFFF]', '', text)  # Emoticons, transport, etc.
        text = re.sub(r'[\u2600-\u26FF]', '', text)           # Misc symbols (BMP)
        text = re.sub(r'[\u2700-\u27BF]', '', text)           # Dingbats
        text = re.sub(r'\uFE0F', '', text)                    # Variation selector

        return text
    

    @classmethod
    def strip_markdown(cls, text: str) -> str:
        """
        Strip markdown formatting from the text.

        Args:
            text (str): The input text with markdown formatting.
        
        Returns:
            str: The text with markdown formatting removed.
        """

        # Headers
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

        # Bold / Italic
        text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
        text = re.sub(r'_{1,3}(.*?)_{1,3}', r'\1', text)

        # Strikethrough
        text = re.sub(r'~~(.*?)~~', r'\1', text)

        # Inline code
        text = re.sub(r'`([^`]+)`', r'\1', text)

        # Code blocks
        text = re.sub(r'```[\s\S]*?```', '', text)

        # Blockquotes
        text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)

        # Bullet points / unordered lists
        text = re.sub(r'^[\*\-\+]\s+', '', text, flags=re.MULTILINE)

        # Numbered lists
        text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)

        # Horizontal rules
        text = re.sub(r'^[-\*_]{3,}\s*$', '', text, flags=re.MULTILINE)

        # Links [text](url) → text
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

        # Images ![alt](url) → entfernen
        text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', text)

        # HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        return text
