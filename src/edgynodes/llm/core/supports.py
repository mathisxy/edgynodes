from pydantic import BaseModel

class Supports(BaseModel):

    vision: bool = True
    audio: bool = False
    streaming: bool = True
    remote_image_urls: bool = True