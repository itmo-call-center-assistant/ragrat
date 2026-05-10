import json
from pathlib import Path

import numpy as np
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastrtc import ReplyOnPause, Stream
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

curr_dir = Path(__file__).parent


def detection(audio: tuple[int, np.ndarray]):
    print("detect", audio)
    yield audio


stream = Stream(handler=ReplyOnPause(detection), modality="audio", mode="send")


class Message(BaseModel):
    role: str
    content: str


class InputData(BaseModel):
    webrtc_id: str
    chatbot: list[Message]


app = FastAPI()
stream.mount(app)

static = StaticFiles(directory="ui", html=True)
app.mount("/ui", static)


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
            yield f"event: output\ndata: {json.dumps(chatbot[-1])}\n\n"

    return StreamingResponse(output_stream(), media_type="text/event-stream")
