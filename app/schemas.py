from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class Persona(BaseModel):
    name: str
    age: int
    location: str
    occupation: str
    tone: str


class Message(BaseModel):
    role: str
    text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class IngestRequest(BaseModel):
    session_id: str
    message: str


class ExtractedIntel(BaseModel):
    bank_accounts: List[str] = []
    ifsc_codes: List[str] = []
    upi_ids: List[str] = []
    urls: List[str] = []
    emails: List[str] = []
    phones: List[str] = []


class IngestResponse(BaseModel):
    session_id: str
    detected_scam: bool
    risk_score: int
    persona: Persona
    agent_reply: str
    extracted: ExtractedIntel
    conversation: List[Message]


class StartSessionResponse(BaseModel):
    session_id: str
    persona: Persona
    message: str
