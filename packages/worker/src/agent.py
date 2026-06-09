import asyncio
import tempfile
from pathlib import Path
from typing import Protocol

import numpy as np
from fastrtc import AdditionalOutputs, get_current_context
from openai import AsyncOpenAI
from ragrat_shared.db import search as do_search
from scipy.io import wavfile

from .asr import get_model
from .config import settings
from .schemas import Message, RetrievedChunks


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
            api_key=settings.llm.api_key,
            base_url=settings.llm.base_url,
        )
        self._model = settings.llm.model

    async def summarize(self, transcripts: list[str], chunks: list[dict]) -> str:
        query = " ".join(transcripts)
        chunks_text = "\n\n".join(f"[{i + 1}] {c['text']}" for i, c in enumerate(chunks))
        response = await self._inner.responses.create(
            model=self._model,
            temperature=settings.llm.temperature,
            input=(
                f'Ответь на вопрос клиента: "{query}" коротко и верно. '
                "Используй ТОЛЬКО информацию из указанного контекста."
                "Не добавляй информацю, не указанную в контексте.\n\n"
                f"Контекст:\n{chunks_text}\n\n"
                "Ответ:"
            ),
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )
        return response.output_text


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

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wavfile.write(tmp.name, sr, audio_data.squeeze())
            tmp_path = tmp.name
        transcription = get_model().model.transcribe(tmp_path)
    finally:
        if tmp_path is not None:
            Path(tmp_path).unlink(missing_ok=True)

    if transcription:
        session_states[webrtc_id]["transcripts"].append(transcription)
        yield AdditionalOutputs(Message(role="user", content=transcription))
        chunks = do_search(transcription)
        if chunks:
            yield AdditionalOutputs(RetrievedChunks(chunks=chunks))
            llm = get_llm()
            summary = await llm.summarize(session_states[webrtc_id]["transcripts"], chunks)
            yield AdditionalOutputs(Message(role="assistant", content=summary))
    yield audio
