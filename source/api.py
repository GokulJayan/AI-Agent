import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from .agent_service import stream_events


WEB_ROOT = Path(__file__).resolve().parent.parent / "web"
app = FastAPI(title="NVIDIA AI Agent", version="0.1.0")
app.mount("/static", StaticFiles(directory=WEB_ROOT), name="static")


class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=12000)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat")
def chat(request: ChatRequest):
    def event_stream():
        for event in stream_events(request.prompt.strip()):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/")
def index():
    return FileResponse(WEB_ROOT / "index.html")
