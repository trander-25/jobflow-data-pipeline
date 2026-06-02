from pydantic import BaseModel
from typing import Optional, List


class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
