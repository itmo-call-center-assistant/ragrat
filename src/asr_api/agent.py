import asyncio
import os
import tempfile
from typing import Protocol

import numpy as np
from fastrtc import AdditionalOutputs, get_current_context
from openai import AsyncOpenAI
from pydantic import BaseModel
from scipy.io import wavfile

from src.document_store import search as do_search

_filter_model = None
_filter_lock: asyncio.Lock | None = None


def _get_filter_lock() -> asyncio.Lock:
    global _filter_lock
    if _filter_lock is None:
        _filter_lock = asyncio.Lock()
    return _filter_lock


def set_filter_model(model):
    global _filter_model
    _filter_model = model


async def should_search(transcription: str) -> bool:
    global _filter_model
    lock = _get_filter_lock()

    if _filter_model is None:
        from llama_cpp import Llama

        _filter_model = Llama.from_pretrained(
            repo_id="LiquidAI/LFM2.5-350M-GGUF",
            filename="LFM2.5-350M-Q4_K_M.gguf",
        )

    async with lock:
        response = _filter_model.create_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a binary classifier. Decide if the following user query "
                        "requires searching a knowledge base for additional context. "
                        "Answer with ONLY YES or NO."
                    ),
                },
                {
                    "role": "user",
                    "content": transcription,
                },
            ],
            max_tokens=4,
            temperature=0.0,
        )
    answer = response["choices"][0]["message"]["content"].strip().upper()
    return answer == "YES"


class Message(BaseModel):
    role: str
    content: str


class RetrievedChunks(BaseModel):
    role: str = "retrieved_chunks"
    chunks: list[dict]


class LLMClient(Protocol):
    async def summarize(self, transcripts: list[str], chunks: list[dict]) -> str: ...


_current_llm: LLMClient | None = None


def get_llm() -> LLMClient:
    if _current_llm is None:
        raise RuntimeError("No LLM client set")
    return _current_llm


def set_llm(client: LLMClient) -> None:
    global _current_llm
    _current_llm = client


class OpenAIClient:
    def __init__(self):
        self._inner = AsyncOpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            base_url=os.environ.get("OPENAI_API_BASE"),
        )
        self._model = os.environ["OPENAI_MODEL"]

    async def summarize(self, transcripts: list[str], chunks: list[dict]) -> str:
        query = " ".join(transcripts)
        chunks_text = "\n\n".join(f"[{i + 1}] {c['text']}" for i, c in enumerate(chunks))
        response = await self._inner.responses.create(
            model=self._model,
            input=(
                f'Based on the user\'s transcripts: "{query}", summarize the following '
                f"retrieved context chunks in a concise and relevant way. Focus on "
                f"information that directly answers or relates to the query.\n\n"
                f"Retrieved chunks:\n{chunks_text}\n\nSummary:"
            ),
        )
        return response.output_text


model = None


def get_model():
    if model is None:
        raise RuntimeError("ASR model not set")
    return model


def set_model(m):
    global model
    model = m


session_states: dict[str, dict] = {}

_stream = None


def set_stream(s):
    global _stream
    _stream = s


async def _cleanup_session(webrtc_id: str):
    output = _stream.additional_outputs.get(webrtc_id)
    if output:
        await output.quit.wait()
    session_states.pop(webrtc_id, None)


async def spawn_cleanup(webrtc_id: str):
    asyncio.create_task(_cleanup_session(webrtc_id))


async def detection(audio: tuple[int, np.ndarray]):
    ctx = get_current_context()
    webrtc_id = ctx.webrtc_id

    if webrtc_id not in session_states:
        session_states[webrtc_id] = {"transcripts": []}

    asyncio.create_task(_cleanup_session(webrtc_id))

    sr, audio_data = audio

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wavfile.write(tmp.name, sr, audio_data.squeeze())
        transcription = get_model().model.transcribe(tmp.name)

    if transcription:
        session_states[webrtc_id]["transcripts"].append(transcription)
        yield AdditionalOutputs(Message(role="user", content=transcription))
        if await should_search(transcription):
            chunks = do_search(transcription)
            if chunks:
                yield AdditionalOutputs(RetrievedChunks(chunks=chunks))
                llm = get_llm()
                summary = await llm.summarize(session_states[webrtc_id]["transcripts"], chunks)
                yield AdditionalOutputs(Message(role="assistant", content=summary))
    yield audio
