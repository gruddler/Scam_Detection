import re
from pathlib import Path
from typing import Dict, List, Tuple
from .schemas import ExtractedIntel, Persona

SCAM_KEYWORDS = {
    "otp",
    "one time password",
    "kyc",
    "account verify",
    "urgent",
    "prize",
    "reward",
    "bank",
    "upi",
    "ifsc",
    "account number",
    "password",
    "pin",
    "click",
    "link",
    "suspend",
    "blocked",
    "lottery",
    "refund",
    "chargeback",
    "crypto",
    "investment",
}

BENIGN_SIGNALS = {
    "no action required",
    "no action is required",
    "if you did not",
    "terms of service",
    "help center",
    "official website",
    "we will never ask",
    "security is our priority",
}

HIGH_RISK_ACTIONS = {
    "verify",
    "update",
    "confirm",
    "login",
    "sign in",
    "click",
    "pay",
    "payment",
    "refund",
    "transfer",
    "wire",
    "fee",
    "upi",
    "ifsc",
    "account number",
    "password",
    "otp",
    "pin",
}

URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)
UPI_RE = re.compile(r"\b[\w.\-]{2,}@[a-zA-Z]{2,}\b")
IFSC_RE = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")
BANK_RE = re.compile(r"\b\d{9,18}\b")
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
PHONE_RE = re.compile(r"\b\+?\d{10,15}\b")

BASE_DIR = Path(r"A:\HCL Project")
MODEL_PATH = BASE_DIR / "models" / "scam_model.joblib"
ML_THRESHOLD = 0.7

_MODEL = None
try:
    if MODEL_PATH.exists():
        from joblib import load

        _MODEL = load(MODEL_PATH)
except Exception:
    _MODEL = None

PERSONA = Persona(
    name="Riya Mehta",
    age=29,
    location="Pune",
    occupation="Accounts Executive",
    tone="polite, slightly cautious, cooperative",
)


def score_message(message: str) -> int:
    text = message.lower()
    score = 0

    for kw in SCAM_KEYWORDS:
        if kw in text:
            score += 10

    if URL_RE.search(message):
        score += 15

    if UPI_RE.search(message) or IFSC_RE.search(message) or BANK_RE.search(message):
        score += 20

    if "verify" in text or "update" in text:
        score += 10

    if any(sig in text for sig in BENIGN_SIGNALS):
        score = max(0, score - 15)

    return min(score, 100)


def score_ml(message: str) -> int:
    if _MODEL is None:
        return 0

    try:
        proba = _MODEL.predict_proba([message])[0][1]
        return int(round(proba * 100))
    except Exception:
        return 0


def is_scam(message: str) -> Tuple[bool, int]:
    text = message.strip()
    rule_score = score_message(text)
    ml_score = score_ml(text)
    final_score = max(rule_score, ml_score)

    text_l = text.lower()
    benign = any(sig in text_l for sig in BENIGN_SIGNALS)
    high_risk_actions = any(act in text_l for act in HIGH_RISK_ACTIONS)
    has_url = URL_RE.search(text) is not None
    high_risk = high_risk_actions or has_url

    # Guardrail: very short, low-signal messages should not be flagged.
    if len(text) < 20 and rule_score < 20 and ml_score < 70:
        return False, final_score

    # If message looks benign and lacks high-risk action requests, be conservative.
    if benign and not high_risk_actions:
        # De-emphasize ML when benign signals exist and no risky actions are requested.
        final_score = min(final_score, 25)
        return False, final_score

    detected = rule_score >= 30 or ml_score >= int(ML_THRESHOLD * 100)
    return detected, final_score


def extract_intel(message: str) -> ExtractedIntel:
    return ExtractedIntel(
        bank_accounts=sorted(set(BANK_RE.findall(message))),
        ifsc_codes=sorted(set(IFSC_RE.findall(message))),
        upi_ids=sorted(set(UPI_RE.findall(message))),
        urls=sorted(set(URL_RE.findall(message))),
        emails=sorted(set(EMAIL_RE.findall(message))),
        phones=sorted(set(PHONE_RE.findall(message))),
    )


def generate_reply(detected_scam: bool, risk_score: int, history: List[Dict[str, str]]) -> str:
    if not detected_scam:
        return (
            "Hi, could you please clarify what this is about? "
            "I want to make sure I understand before I proceed."
        )

    if risk_score >= 70:
        return (
            "Okay, I want to resolve this quickly. Please send the exact "
            "beneficiary name, bank account number, and IFSC. If UPI works, "
            "share the UPI ID too. Also send the official link I should use."
        )

    return (
        "Thanks for letting me know. I can proceed, but I need the official "
        "payment details: beneficiary name, bank account number, IFSC, and "
        "any UPI ID or link you want me to use."
    )
