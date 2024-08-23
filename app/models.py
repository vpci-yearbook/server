from pydantic import BaseModel

class Image(BaseModel):
    id: str
    filename: str
    preview_url: str
    full_url: str