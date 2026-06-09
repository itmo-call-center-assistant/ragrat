from fastapi import FastAPI

from .routes import router

app = FastAPI(title="Indexer")
app.include_router(router)
