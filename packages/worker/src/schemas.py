from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


class RetrievedChunks(BaseModel):
    role: str = "retrieved_chunks"
    chunks: list[dict]


class InputData(BaseModel):
    webrtc_id: str
    chatbot: list[Message]
