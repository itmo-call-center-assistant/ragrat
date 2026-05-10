import numpy as np
from fastapi import FastAPI
from fastrtc import ReplyOnPause, Stream

app = FastAPI()


def detection(audio: tuple[int, np.ndarray]):
    print("detect", audio)
    yield audio


stream = Stream(handler=ReplyOnPause(detection), modality="audio", mode="send")

stream.ui.launch()

# @app.get("/")
# def read_root():
#     return {"status": "ok"}
