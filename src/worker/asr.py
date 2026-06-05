import asyncio

from transformers import AutoModel

MODEL_NAME = "ai-sage/GigaAM-v3"
MODEL_REVISION = "e2e_rnnt"

_model = None


async def load_model() -> AutoModel:
    global _model
    print(f"Loading ASR model: {MODEL_NAME}")
    _model = await asyncio.to_thread(
        AutoModel.from_pretrained,
        MODEL_NAME,
        revision=MODEL_REVISION,
        trust_remote_code=True,
    )
    _model.eval()
    print("ASR model loaded")
    return _model


def get_model() -> AutoModel:
    if _model is None:
        raise RuntimeError("ASR model not set")
    return _model
