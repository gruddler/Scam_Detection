import json
from datetime import datetime
from typing import Dict, List
from uuid import uuid4

from .config import EVENTS_FILE
from .schemas import Message, Persona
from .engines import PERSONA

_sessions: Dict[str, List[Message]] = {}


def start_session() -> str:
    session_id = str(uuid4())
    _sessions[session_id] = []
    add_message(session_id, "system", f"Persona: {PERSONA.json()}")
    return session_id


def get_conversation(session_id: str) -> List[Message]:
    return _sessions.get(session_id, [])


def add_message(session_id: str, role: str, text: str) -> None:
    message = Message(role=role, text=text)
    _sessions.setdefault(session_id, []).append(message)
    append_event(
        {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "role": role,
            "text": text,
        }
    )


def append_event(payload: Dict) -> None:
    with EVENTS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
