import asyncio
import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastrtc import AdditionalOutputs, ReplyOnPause, Stream, get_current_context
from openai import AsyncOpenAI
from pydantic import BaseModel
from scipy.io import wavfile
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from transformers import AutoModel

from src.document_store.routes import do_search
from src.document_store.routes import router as document_router

curr_dir = Path(__file__).parent

openai_client = AsyncOpenAI(
    api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ.get("OPENAI_API_BASE")
)

session_states: dict[str, dict] = {}
_cleanup_started: set[str] = set()


async def summarize_chunks(transcripts: list[str], chunks: list[dict]) -> str:
    query = " ".join(transcripts)
    chunks_text = "\n\n".join(f"[{i + 1}] {c['text']}" for i, c in enumerate(chunks))
    response = await openai_client.responses.create(
        model=os.environ["OPENAI_MODEL"],
        input=f"""
Based on the user's transcripts: "{query}", summarize the following retrieved context
chunks in a concise and relevant way. Focus on information that directly answers
or relates to the query. Respond in russian.

Retrieved chunks:
{chunks_text}

Summary:""",
    )
    return response.output_text


async def _cleanup_session(webrtc_id: str):
    output = stream.additional_outputs.get(webrtc_id)
    if output:
        await output.quit.wait()
    session_states.pop(webrtc_id, None)
    _cleanup_started.discard(webrtc_id)


model: AutoModel | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    model_name = "ai-sage/GigaAM-v3"
    print(f"Loading ASR model: {model_name}")
    revision = "e2e_rnnt"
    model = AutoModel.from_pretrained(
        model_name,
        revision=revision,
        trust_remote_code=True,
        low_cpu_mem_usage=False,
    )
    model.eval()
    app.state.asr_model = model
    print("ASR model loaded")
    yield


async def detection(audio: tuple[int, np.ndarray]):
    ctx = get_current_context()
    webrtc_id = ctx.webrtc_id

    if webrtc_id not in session_states:
        session_states[webrtc_id] = {"transcripts": []}

    if webrtc_id not in _cleanup_started:
        _cleanup_started.add(webrtc_id)
        asyncio.create_task(_cleanup_session(webrtc_id))

    print("detection called")
    sr, audio_data = audio
    print(f"Audio shape: {audio_data.shape}, dtype: {audio_data.dtype}, sr: {sr}")

    import os

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp_path = f.name
    wavfile.write(tmp_path, sr, audio_data.squeeze())
    print(f"File size: {os.path.getsize(tmp_path)}")

    transcription = model.model.transcribe(tmp_path)
    print("ASR transcription:", transcription)

    if transcription:
        session_states[webrtc_id]["transcripts"].append(transcription)
        message = Message(role="user", content=transcription)
        yield AdditionalOutputs(message)
        chunks = do_search(transcription)
        if chunks:
            yield AdditionalOutputs(RetrievedChunks(chunks=chunks))
            summary = await summarize_chunks(session_states[webrtc_id]["transcripts"], chunks)
            yield AdditionalOutputs(Message(role="assistant", content=summary))
    yield audio


stream = Stream(handler=ReplyOnPause(detection), modality="audio", mode="send")


class Message(BaseModel):
    role: str
    content: str


class RetrievedChunks(BaseModel):
    role: str = "retrieved_chunks"
    chunks: list[dict]


class InputData(BaseModel):
    webrtc_id: str
    chatbot: list[Message]


app = FastAPI(lifespan=lifespan)
stream.mount(app)

static = StaticFiles(directory="ui", html=True)
app.mount("/ui", static)
app.include_router(document_router)


class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        if request.url.path.startswith("/ui"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response


app.add_middleware(NoCacheMiddleware)


@app.post("/input_hook")
async def _(body: InputData):
    stream.set_input(body.webrtc_id, body.model_dump()["chatbot"])
    return {"status": "ok"}


@app.get("/outputs")
def _(webrtc_id: str):
    async def output_stream():
        async for output in stream.output_stream(webrtc_id):
            chatbot = output.args[0]
            yield f"event: output\ndata: {chatbot.model_dump_json()}\n\n"

    return StreamingResponse(output_stream(), media_type="text/event-stream")
