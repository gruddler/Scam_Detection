from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .schemas import IngestRequest, IngestResponse, StartSessionResponse
from .engines import PERSONA, extract_intel, generate_reply, is_scam
from .storage import add_message, get_conversation, start_session
from .config import WEB_DIR

app = FastAPI(title="Agentic Honeypot", version="0.2.0")

app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


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
