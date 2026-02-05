from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .schemas import IngestRequest, IngestResponse, StartSessionResponse
from .engines import PERSONA, extract_intel, generate_reply, is_scam
from .storage import add_message, get_conversation, start_session
from .config import WEB_DIR

app = FastAPI(title="Agentic Honeypot", version="0.2.0")

app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

API_KEY_ENV = "API_KEY"


def require_api_key(request: Request) -> None:
    expected = request.app.state.api_key
    if not expected:
        return
    provided = request.headers.get("x-api-key")
    if provided != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.on_event("startup")
def load_api_key() -> None:
    import os

    app.state.api_key = os.getenv(API_KEY_ENV, "")


class JudgeMessage(BaseModel):
    sender: str
    text: str
    timestamp: Optional[int] = None


class JudgeRequest(BaseModel):
    sessionId: str
    message: JudgeMessage
    conversationHistory: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}


@app.get("/")
def index():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/start", response_model=StartSessionResponse)
def start():
    session_id = start_session()
    greeting = (
        f"Hello, this is {PERSONA.name}. I received a message about my account. "
        "Can you explain what I need to do?"
    )
    add_message(session_id, "assistant", greeting)
    return StartSessionResponse(session_id=session_id, persona=PERSONA, message=greeting)


@app.post("/ingest", response_model=IngestResponse)
def ingest(payload: IngestRequest):
    session_id = payload.session_id
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    add_message(session_id, "scammer", payload.message)

    detected, score = is_scam(payload.message)
    extracted = extract_intel(payload.message)
    reply = generate_reply(detected, score, [m.dict() for m in get_conversation(session_id)])

    add_message(session_id, "assistant", reply)

    conversation = get_conversation(session_id)

    return IngestResponse(
        session_id=session_id,
        detected_scam=detected,
        risk_score=score,
        persona=PERSONA,
        agent_reply=reply,
        extracted=extracted,
        conversation=conversation,
    )


@app.post("/respond")
def respond(payload: JudgeRequest, request: Request):
    require_api_key(request)
    text = payload.message.text
    detected, score = is_scam(text)
    reply = generate_reply(detected, score, payload.conversationHistory)
    return {"status": "success", "reply": reply}


@app.post("/")
def root_post(payload: JudgeRequest, request: Request):
    return respond(payload, request)
