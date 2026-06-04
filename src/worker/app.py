from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastrtc import ReplyOnPause, Stream
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from transformers import AutoModel

from . import agent


class InputData(BaseModel):
    webrtc_id: str
    chatbot: list[agent.Message]


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    agent.set_model(model)
    agent.set_llm(agent.OpenAIClient())
    yield


stream = Stream(handler=ReplyOnPause(agent.detection), modality="audio", mode="send")
agent.set_stream(stream)

app = FastAPI(lifespan=lifespan)
stream.mount(app)

static = StaticFiles(directory="ui", html=True)
app.mount("/ui", static)


class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
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
