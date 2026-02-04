const startBtn = document.getElementById("startBtn");
const healthBtn = document.getElementById("healthBtn");
const clearBtn = document.getElementById("clearBtn");
const copyIntelBtn = document.getElementById("copyIntelBtn");
const exportBtn = document.getElementById("exportBtn");
const chat = document.getElementById("chat");
const typingEl = document.getElementById("typing");
const messageForm = document.getElementById("messageForm");
const messageInput = document.getElementById("messageInput");
const persona = document.getElementById("persona");
const sessionIdEl = document.getElementById("sessionId");
const statusEl = document.getElementById("status");
const detectedEl = document.getElementById("detected");
const scoreEl = document.getElementById("score");
const confidenceFill = document.getElementById("confidenceFill");
const confidenceLabel = document.getElementById("confidenceLabel");
const extractedEl = document.getElementById("extracted");
const agentReplyEl = document.getElementById("agentReply");
const msgCountEl = document.getElementById("msgCount");
const linkCountEl = document.getElementById("linkCount");
const idCountEl = document.getElementById("idCount");

let sessionId = null;
let messageCount = 0;
let totalLinks = 0;
let totalIds = 0;
let lastResponse = null;

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.textContent = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
  messageCount += 1;
  msgCountEl.textContent = String(messageCount);
}

function setStatus(text) {
  statusEl.textContent = `Status: ${text}`;
}

function setTyping(isTyping) {
  typingEl.classList.toggle("hidden", !isTyping);
}

function pulseScore() {
  scoreEl.classList.remove("pulse");
  void scoreEl.offsetWidth;
  scoreEl.classList.add("pulse");
}

function updateConfidence(score) {
  if (!confidenceFill || !confidenceLabel) return;
  const value = Number(score);
  const safeValue = Number.isFinite(value) ? value : 0;
  const clamped = Math.max(0, Math.min(100, safeValue));
  confidenceFill.style.width = `${clamped}%`;
  confidenceLabel.textContent = `Confidence: ${clamped} percent`;
}

function normalizeExtracted(extracted) {
  if (!extracted || typeof extracted !== "object") return null;
  const urls = Array.isArray(extracted.urls) ? extracted.urls : [];
  const upi = Array.isArray(extracted.upi_ids) ? extracted.upi_ids : [];
  const banks = Array.isArray(extracted.bank_accounts) ? extracted.bank_accounts : [];
  const ifsc = Array.isArray(extracted.ifsc_codes) ? extracted.ifsc_codes : [];
  return { urls, upi, banks, ifsc };
}

async function checkHealth() {
  setStatus("Checking health");
  const res = await fetch("/health");
  const data = await res.json();
  setStatus(data.status === "ok" ? "Healthy" : "Unhealthy");
}

async function startSession() {
  setStatus("Starting session");
  const res = await fetch("/start", { method: "POST" });
  const data = await res.json();
  sessionId = data.session_id;
  persona.textContent = `${data.persona.name}, ${data.persona.age} | ${data.persona.location} | ${data.persona.occupation} | ${data.persona.tone}`;
  sessionIdEl.textContent = `Session: ${sessionId}`;
  addMessage("assistant", data.message);
  setStatus("Session ready");
}

async function sendMessage(text) {
  if (!sessionId) {
    addMessage("system", "Start a session first.");
    return;
  }

  addMessage("scammer", text);
  messageInput.value = "";
  setStatus("Analyzing message");
  setTyping(true);

  const res = await fetch("/ingest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message: text }),
  });

  const data = await res.json();
  lastResponse = data;
  detectedEl.textContent = data.detected_scam ? "Yes" : "No";
  scoreEl.textContent = String(data.risk_score);
  updateConfidence(data.risk_score);
  extractedEl.textContent = JSON.stringify(data.extracted, null, 2);
  agentReplyEl.textContent = data.agent_reply;
  addMessage("assistant", data.agent_reply);
  setTyping(false);
  setStatus("Waiting");
  pulseScore();

  const extracted = normalizeExtracted(data.extracted) || { urls: [], upi: [], banks: [], ifsc: [] };
  totalLinks += extracted.urls.length;
  totalIds += extracted.upi.length + extracted.banks.length + extracted.ifsc.length;
  linkCountEl.textContent = String(totalLinks);
  idCountEl.textContent = String(totalIds);
}

async function copyIntel() {
  try {
    await navigator.clipboard.writeText(extractedEl.textContent || "{}");
    setStatus("Intel copied");
  } catch (err) {
    setStatus("Copy failed");
  }
}

function exportSession() {
  if (!lastResponse) {
    setStatus("No session data to export");
    return;
  }
  const payload = {
    exported_at: new Date().toISOString(),
    session_id: lastResponse.session_id || sessionId,
    detected_scam: lastResponse.detected_scam,
    risk_score: lastResponse.risk_score,
    persona: lastResponse.persona,
    extracted: lastResponse.extracted,
    conversation: lastResponse.conversation,
  };

  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `session_${payload.session_id || "export"}.json`;
  a.click();
  URL.revokeObjectURL(url);
  setStatus("Session exported");
}

startBtn.addEventListener("click", () => startSession());
healthBtn.addEventListener("click", () => checkHealth());
clearBtn.addEventListener("click", () => {
  chat.innerHTML = "";
  detectedEl.textContent = "-";
  scoreEl.textContent = "-";
  updateConfidence(0);
  extractedEl.textContent = "{}";
  agentReplyEl.textContent = "-";
  messageCount = 0;
  totalLinks = 0;
  totalIds = 0;
  lastResponse = null;
  msgCountEl.textContent = "0";
  linkCountEl.textContent = "0";
  idCountEl.textContent = "0";
  setTyping(false);
  setStatus("Idle");
});
copyIntelBtn.addEventListener("click", () => copyIntel());
exportBtn.addEventListener("click", () => exportSession());

messageForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = messageInput.value.trim();
  if (!text) return;
  sendMessage(text);
});
