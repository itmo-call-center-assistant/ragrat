from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastrtc import ReplyOnPause, Stream

from . import agent
from .asr import load_model
from .schemas import InputData
from .static import mount_static


@asynccontextmanager
async def lifespan(app: FastAPI):
    await load_model()
    agent.set_llm(agent.OpenAIClient())
    yield


stream = Stream(handler=ReplyOnPause(agent.detection), modality="audio", mode="send")
agent.set_stream(stream)

app = FastAPI(lifespan=lifespan)
stream.mount(app)

mount_static(app)


@app.post("/input_hook")
async def _(body: InputData):
    stream.set_input(body.webrtc_id, body.chatbot)
    return {"status": "ok"}


@app.get("/outputs")
def _(webrtc_id: str):
    async def output_stream():
        async for output in stream.output_stream(webrtc_id):
            chatbot = output.args[0]
            yield f"event: output\ndata: {chatbot.model_dump_json()}\n\n"

    return StreamingResponse(output_stream(), media_type="text/event-stream")
