# Agentic Honey-Pot (Simple FastAPI)

Minimal, workable honeypot service that detects scam patterns, keeps a believable persona, and continues the conversation to extract intel (bank accounts, IFSC, UPI IDs, phishing links). It stores events as JSONL and returns a structured JSON response.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Endpoints

- `GET /health`
- `POST /start` -> starts a session and returns persona + greeting
- `POST /ingest` -> send scammer message, receive agent reply and extracted intel

### Example

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/start -Method Post
```

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/ingest -Method Post -Body (
  @{ session_id = "<SESSION_ID>"; message = "We need your bank account and IFSC. Click https://phish.tld" } | ConvertTo-Json
) -ContentType "application/json"
```

## Data

Events are appended to `A:\HCL Project\data\events.jsonl`.

## Notes

- No Mock Scammer API spec was provided, so `/ingest` simulates incoming scammer messages.
- You can later plug in a real API client and call it from a scheduler or webhook.
