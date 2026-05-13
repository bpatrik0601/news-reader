from pydantic import BaseModel
from typing import Optional


class Article(BaseModel):
    source: str
    title: str
    url: str
    published_at: Optional[str]
    content: str
