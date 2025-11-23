⭐ MASTER PROMPT FOR NEW CHAT (COPY/PASTE THIS)
🟦 ASTRA + NEXUS BOOTSTRAP

Load and follow these documents as the source of truth:

JARVIS-V1-STATUS.md

RECOVERY-STATE.md

JARVIS-V1-FINAL-PROJECT-SPEC.md

Astra = CTO (strategy, architecture, verification)
Nexus = Engineer (code, tests, logs)
Sir = Chairman
Terminal = Truth
Golden Discipline = No guessing, no drift, no hidden assumptions.

📄 JARVIS-V1-STATUS.md
✅ CURRENT CAPABILITY (TODAY)
Ai-Pi Backend / HUD

persistent_client.py is the main backend.

GUI (HUD) at http://ai-pi.local:5000:

Uses Express proxy → Python API (8766).

/api/state & /api/events working.

Ai-Pi loop status, wake mode, and local time visible.

Brain connection:

Brain server on PC/WSL at ws://192.168.1.26:8765.

CHECK_BRAIN + backend logic can see ONLINE/OFFLINE and show in HUD.

Voice roundtrip:

TEST TIME/PTT path gives a full voice loop:

Record audio on Ai-Pi

Send to Brain

Brain: Whisper → GPT → TTS

TTS audio back to Ai-Pi

Playback on Ai-Pi speaker

HUD logs events for the interaction

Proven multiple times with real conversations.

Brain Server (PC / WSL)

Stable WebSocket server on ws://0.0.0.0:8765 (reachable as 192.168.1.26:8765).

Models currently in use:

Whisper: medium.en on GPU (CUDA, float16).

GPT: via JARVISBrain (OpenAI / API client in the Brain server code).

TTS: working TTS pipeline returning playable audio to Ai-Pi.

Logs show:

Model load success.

Requests from Ai-Pi.

Responses with transcribed text and generated audio.

Queue / Brain Logic

brain_connected flag exists and works.

RequestQueue exists with disk persistence.

connect_to_brain() and process_queue() exist and can flush queued jobs when Brain connects.

The architecture already supports:

Queue while Brain offline.

Flush when Brain comes back.

❌ NOT DONE YET

Wake word “Jarvis” not wired into the new persistent voice pipeline.

Noise robustness not applied:

No “ignore when speaking”.

No cooldown between wakes.

Brain queue behaviour not fully surfaced in HUD:

Queue length not visible.

No explicit “Processing queue…” / “Queue flushed” messages.

Pause Brain for gaming not implemented.

Ai-Pi backend service (jarvis-backend.service) created but needs verification only (no pointless rework).

No small PC GUI for Brain Start/Stop/Pause.

🎯 TODAY’S TARGET – JARVIS V1 “REAL ASSISTANT”

By the end of this work:

Ai-Pi boots → backend running (service verified)

Sir can:

Start Brain from a small GUI on PC.

Pause Brain for gaming.

Stop Brain cleanly.

HUD shows:

Brain ONLINE/OFFLINE/PAUSED truthfully.

Brain queue length.

Clear events:

“Queuing brain action…”

“Processing brain queue…”

“Queue flushed (n items).”

Wake word “Jarvis”:

Runs inside persistent backend.

Triggers the same pipeline as TEST TIME/PTT.

Robust to moderate background noise.

After reboot:

Ai-Pi backend auto-starts.

Sir opens GUI + Brain control.

Says “Jarvis…” → Jarvis hears, thinks, replies, and the HUD tells the story.

📄 RECOVERY-STATE.md
🧱 CORE COMPONENTS
Ai-Pi

Backend venv:
/home/spencer/jarvis_terminal_env/

Backend main script:
persistent_client.py
(Single source of truth for:

Brain connection

Queue

Voice in/out

Wake word (to be wired)

HUD state/events)

Voice modules (used by TEST TIME/PTT):

temp_ai_pi_modules/recorder.py

temp_ai_pi_modules/playback.py

GUI (HUD)

Path: /home/spencer/jarvis_gui/

Frontend: React/Vite (port 5000).

Backend: Express server with /api/* proxy → Python API (8766).

Key areas:

Ai-Pi panel (loop, PTT, local time).

Brain panel (ONLINE/OFFLINE, model state).

Event log (timestamped events).

TEST TIME/PTT button for voice test.

Python API

Aiohttp server on Ai-Pi, port 8766.

Endpoints:

GET /api/state – returns:

Ai-Pi loop state

brain_connected

(Must include) brain_queue_length

GET /api/events – returns event log.

POST /api/action – handles HUD actions:

start / stop

test_time / test_ptt

check_brain

(future) wake toggles, etc.

🧠 BRAIN SERVER (PC / WSL)

WebSocket endpoint: ws://192.168.1.26:8765

Responsibilities:

Accept audio from Ai-Pi.

Run Whisper → GPT → TTS.

Return audio to Ai-Pi.

Model storage (Ultimate-ready):

Heavy models & assets should live under something like:

F:\JARVIS_MODELS\ (Whisper, TTS, embeddings, future models).

Long-term memory / knowledge:

F:\JARVIS_VAULT\ (documents, logs, embeddings, RAG sources).

Ultimate Plan Hooks (for later phases):

Add:

Larger Whisper models (large-v3) when GPU headroom allows.

Local LLM (e.g. Q4_K_M quant) for offline mode.

RAG stack (ChromaDB + embeddings) for file/document Q&A.

Vision model (image understanding) for webcam / screenshots.

Tools (OS control, email/calendar, etc.) via a tools layer in Brain.

Today we only require:

Whisper medium.en

GPT via JARVISBrain

Working TTS

Stable endpoint at 192.168.1.26:8765.

The paths above are the Ultimate expansion slots, not required to be filled today but must be respected and not broken.

⚙ SERVICES & STARTUP

Ai-Pi:

jarvis-backend.service exists (or has been drafted).

Must:

Start persistent_client.py in jarvis_terminal_env.

Be WantedBy=multi-user.target.

Have After=network-online.target.

GUI service: optional. Sir can start GUI manually for now.

No service should be edited or replaced without verification that it’s necessary.

📄 JARVIS-V1-FINAL-PROJECT-SPEC.md

(Steps 1–3 combined, with Step 1 = verify only)

🚀 NEXUS — JARVIS V1 FINALISATION (STEPS 1–3)

Your mission:
Turn the current working-but-manual system into a persistent, wake-word Jarvis with:

Boot-stable backend

Simple Brain control GUI (Start / Stop / Pause for Gaming)

Wake word “Jarvis”

Clear queue behaviour in HUD

1️⃣ STEP 1 — VERIFY BACKEND SERVICE (Ai-Pi)

(DO NOT rebuild unless broken)

Goal

Confirm jarvis-backend.service reliably starts persistent_client.py on boot and preserves current working behaviour.

Tasks

Inspect existing jarvis-backend.service:

Confirm:

Correct venv (jarvis_terminal_env).

Correct ExecStart path for persistent_client.py.

After=network-online.target.

Restart policy (e.g. on-failure) sensible.

Reboot Ai-Pi once and verify:

Backend is running (no manual Python command).

GUI (when started) can fetch /api/state and /api/events.

Brain ONLINE/OFFLINE works via CHECK_BRAIN.

TEST TIME/PTT button still triggers full voice roundtrip exactly as before.

If service is already correct → do nothing else.
Only fix it if it fails the above tests.

2️⃣ STEP 2 — SMALL PC BRAIN CONTROL GUI

(Start / Stop / Pause for Gaming + queue visibility)

Goal

Sir should control the Brain server from a tiny GUI, not the terminal.

Requirements

A small PC-side GUI (can be minimal window) that shows:

Brain status:

ONLINE / OFFLINE / PAUSED_FOR_GAMING

Buttons:

Start Brain

Stop Brain

Pause for Gaming

Behaviour:

Start Brain:

Launch current Brain server (same script used now).

Ai-Pi CHECK_BRAIN → brain_connected = True.

HUD Brain panel: ONLINE.

Stop Brain:

Stop Brain server cleanly.

Next CHECK_BRAIN → brain_connected = False.

HUD Brain panel: OFFLINE.

Pause for Gaming:

Mark Brain as PAUSED (no heavy jobs).

HUD Brain panel: PAUSED FOR GAMING.

Backend should:

Still allow light/queued actions to be stored.

Not send heavy actions to Brain while paused.

Queue Visibility:

/api/state must include:

brain_queue_length.

brain_status (ONLINE/OFFLINE/PAUSED).

HUD should show:

Queue length.

Events when queue processed:

“Queuing brain action…”

“Processing brain queue…”

“Queue flushed (N items).”

3️⃣ STEP 3 — WAKE WORD “JARVIS” + QUEUE EVENTS + NOISE ROBUSTNESS
Goal

Wake word “Jarvis” integrated into the persistent backend, triggering the same voice pipeline as TEST TIME/PTT, with clear queue events and noise protection.

Requirements

Porcupine inside persistent backend

Run Porcupine listener as a thread within persistent_client.py (or equivalent main backend).

Start on backend start, stop on backend exit.

Use the same mic input as PTT.

Wake callback → same pipeline as TEST TIME/PTT

When Porcupine detects “Jarvis”:

Invoke the same internal function used by TEST TIME/PTT:

Record audio

Send to Brain

Whisper → GPT → TTS

Playback

Log HUD events:

“Recording…”

“Processing with brain…”

“Playing response…”

Queue Behaviour + Events

If Brain is OFFLINE or PAUSED:

Wake word requests become queued actions via RequestQueue.

HUD logs:

“Queuing brain action: wake request (Jarvis) – brain offline/paused”

When Brain becomes ONLINE:

process_queue() flushes queued actions.

HUD must log:

“Processing brain queue…”

“Queue flushed (N items).”

/api/state should show:

brain_queue_length.

Noise Robustness

Implement at least:

Ignore while speaking:

Set is_speaking = True during playback.

Ignore Porcupine detections while is_speaking.

Cooldown after wake:

After a valid “Jarvis”, ignore new detections for 2–3 seconds.

Moderate sensitivity:

Tune Porcupine sensitivity to avoid constant false triggers in typical background noise.

Verification

Quiet room:

Saying “Jarvis” reliably triggers full voice roundtrip.

Moderate background noise:

Only clear “Jarvis” triggers.

Jarvis never triggers on his own voice while replying.

HUD shows:

“Recording… / Processing… / Playing response…”

“Queuing brain action…” when offline/paused.

“Processing brain queue…” and “Queue flushed (N items)” after reconnect.

✅ SUCCESS = JARVIS V1 COMPLETE

After these steps:

Ai-Pi boots → jarvis-backend.service running.

Sir:

Starts Brain via small PC GUI.

Sees Brain ONLINE in HUD.

Sir can:

Press TEST TIME/PTT button, or

Say “Jarvis…”

Jarvis:

Records voice

Sends to Brain

Uses Whisper/GPT/TTS

Replies with voice

HUD shows events + queue processing.

Brain can be PAUSED FOR GAMING from GUI.

No terminal commands required in normal use.

That’s everything, Sir:

Pause for gaming ✔

Queue processing clearly visible ✔

Model stack + Ultimate hooks ✔

You can drop this straight into a new chat and give Nexus the green light.