# JARVIS MASTER TODO — MERGED (2025-11-21)

This is the merged, canonical TODO list for the Jarvis Hybrid system (Ai-Pi + PC Brain + Vault + HUD). It supersedes earlier scattered notes and should be treated as the single source of truth.

---

## 0. PRIORITIES SNAPSHOT

**Immediate (this weekend / next few days)**
1. STT long-form upgrade (Ai-Pi)
2. Offline asset behaviour fix (Ai-Pi)
3. Voice asset expansion & wiring (Ai-Pi + Brain)
4. Memory-to-Vault workflows polish (Brain)
5. Web Search (Google Free Tier) – design + first implementation (Brain)
6. ModelManager v1 – basic model switching (Brain)

**Near-term**
7. Presence detection via camera (Brain, later Pi)
8. Nightly Astra system check (Pi → Brain)
9. HUD layout & new tabs
10. Email + calendar integration (Brain)

**Later / polish**
11. Conversation mode
12. Mood/stress detection
13. Home Assistant / smart home links

---

## 1. STT & LISTENING (HIGH IMPACT)

### 1.1 Long-form STT Upgrade (Critical)
- Increase maximum utterance duration (target: 15–20 seconds).
- Tune VAD thresholds for:
  - gentle pauses
  - end-of-sentence detection
  - background noise environment
- Ensure Whisper chunk stitching preserves:
  - punctuation
  - numbers
  - names (“Teddy”, “Tabby”, “Jarvis”).
- Add soft timeout:
  - if silence > X seconds → finalize and send text.
- Test set:
  - 10s instruction, 15s instruction, mixed noise.
- Confirm:
  - No truncation mid-sentence.
  - Queue behaviour still correct when Brain offline.

### 1.2 Wake-word & Gaming Mode
- Verify wake detection is not overly sensitive.
- Confirm Gaming mode fully disables:
  - wake-word detection
  - STT capture
- Add subtle audio or HUD cue when Gaming mode is ON/OFF.

---

## 2. OFFLINE BEHAVIOUR & VOICE ASSETS

### 2.1 Offline Logic Fix (Urgent)
Current issue:
- offline.mp3 plays too often (when Brain drops, not just when speaking while offline).

Tasks:
- Trigger offline.mp3 **only** when:
  - wake word is detected,
  - Brain is unreachable,
  - and a voice command is actually captured.
- Do not play offline asset on:
  - temporary link blips without user speech.
- Ensure offline flow:
  1. Wake → capture text.
  2. Detect Brain offline.
  3. Play offline asset.
  4. Log event to HUD.
  5. Add entry to queue.json.

### 2.2 Voice Asset Expansion (Pi)
Add MP3s to `/home/spencer/jarvis_v2/assets/audio/`:

- offline.mp3 *(already present)*
- queue_added.mp3
- queue_purged.mp3
- gaming_on.mp3
- gaming_off.mp3
- shutdown.mp3
- good_morning.mp3
- welcome_back.mp3
- understood.mp3
- processing.mp3
- error_generic.mp3

Wire events:

- Queue item added → `queue_added.mp3`.
- Queue item purged (single) → `queue_purged.mp3`.
- Purge all → same asset or dedicated variant.
- Gaming mode ON/OFF → `gaming_on/off.mp3`.
- Shutdown sequence → `shutdown.mp3`.
- Morning first-boot → `good_morning.mp3`.
- Sir returns to chair after absence → `welcome_back.mp3`.
- When Brain is thinking → `processing.mp3` (optional short blip).
- On generic error → `error_generic.mp3`.

---

## 3. QUEUE & HANDSHAKE

### 3.1 Brain–Queue Handshake (Planned)
- Implement handshake so:
  - Pi sends queued item → Brain.
  - Brain processes and returns explicit ACK (success/failure).
  - Only on ACK(success) does Pi remove the queue item.
- Add queue-sync endpoint:
  - Option to request “resend last N” if desync suspected.
- Logs:
  - Each flush event logged in Vault under `/system/` or `/queue/`.

---

## 4. FILESERVICE & VAULT WORKFLOWS

### 4.1 FileService Polish
- Add dedicated log category:
  - `/logs/` for internal Jarvis logs.
- Add error recording:
  - file write failures
  - invalid path attempts
  - vault-misconfig events.
- Ensure all write operations:
  - use UTC+local timestamp pattern consistently.
- Implement safe append helper for:
  - running logs (e.g. nightly summaries).

### 4.2 Memory-to-Vault Mapping
- Standardise phrases:
  - “Save a note…” → `/notes/`
  - “Observation…” or “log that…” → `/notes/` (with label in file).
  - “Run a system check and save it” → `/system/`.
- Add optional categories via speech:
  - “Tag this note as Teddy.”
  - “Tag this as health.”
- Format inside files:
  - front-matter block with:
    - datetime
    - category
    - source (“voice” / “Dev”)
    - relevance (if provided).

---

## 5. WEB SEARCH (GOOGLE FREE TIER)

### 5.1 SearchService v1
- Implement `search_service.py` on Brain.
- Use:
  - Google Programmable Search (CSE).
- Env configuration:
  - API key and CX ID stored in `~/JARVIS/config/.env`.
- Exposed commands:
  - “!search <query>”
  - “Jarvis, search the web for <query>.”
- Flow:
  1. Fetch top N results (3–5).
  2. Summarise with LLM.
  3. Present short spoken answer.
  4. Save full summary & link list to Vault:
     - `web/YYYY-MM-DD/HHMM_<slug>.md`
- Later:
  - HUD “Web” tab:
    - list of last N web searches
    - click to open local markdown or external links.

---

## 6. MODELMANAGER (MULTI-MODEL ENGINE)

### 6.1 ModelManager v1 (Design & Implement)
- Catalogue installed Ollama models.
- Mark roles:
  - fast / default / creative / reasoning.
- Provide API:
  - `set_model("fast")`
  - `set_model("deep")`
  - `set_model("creative")`
- Add heuristics:
  - Short factual → fast model.
  - Long reflective → deeper model.
  - Storytelling → creative model.
- Logging:
  - Record which model served each request.
- Future GUI:
  - HUD dropdown to override model choice temporarily.

---

## 7. NIGHTLY ASTRA CHECK

### 7.1 Nightly Health Script
- Trigger time: ~02:00.
- Data to capture:
  - Brain online/offline.
  - Queue length.
  - TTS errors count for the day.
  - Pi CPU/RAM/temp.
  - PC CPU/RAM/disk/temp (from Brain).
  - Presence pattern (optional).
- Output:
  - Markdown file saved to:
    - `system/HHMM_AstraNightly.md`.
- Option:
  - voice summary in the morning when Sir appears:
    - “Sir, last night’s health check found everything nominal,” etc.

---

## 8. PRESENCE & CAMERA

### 8.1 Presence Detection v1
- Use existing camera (or future Insta360).
- Simple check:
  - detect whether Sir is present in chair area.
- Logic:
  - If absent for 5 minutes:
    - HUD sleep mode (dim / pause animations).
  - Every 5 minutes:
    - Check again.
  - When presence returns:
    - `welcome_back.mp3`
    - optional short spoken status update.
- Logging:
  - Minimal presence log under `/presence/`.

---

## 9. HUD IMPROVEMENTS

### 9.1 Layout & Tabs
- Add tabs:
  - **Overview** (current)
  - **Notes**
  - **System**
  - **Web**
- Components:
  - Overview:
    - queue
    - events
    - Brain status
    - mode (normal/gaming/offline)
  - Notes:
    - today’s notes list (from Vault or memory API)
  - System:
    - temps
    - utilisation
    - last health check stats
  - Web:
    - last N web searches

### 9.2 Visual Polish
- Improve use of horizontal space.
- Text scaling options.
- Toggle full-screen.
- Optional reduced-contrast “night mode”.

---

## 10. EMAIL & CALENDAR

### 10.1 Email v1 (BT Mail + Gmail)
- Implement `email_service.py` on Brain.
- Capabilities (v1):
  - Read unread messages summary.
  - Identify possible spam/phishing.
  - Archive or mark-as-read (if APIs allow).
- Voice commands examples:
  - “Jarvis, summarise my new emails.”
  - “Which messages look suspicious?”
- Output:
  - Spoken summary.
  - File in Vault: `email/YYYY-MM-DD/HHMM_summary.md`.

### 10.2 Calendar v1
- Implement `calendar_service.py` on Brain.
- Capabilities:
  - Today’s events.
  - Tomorrow’s events.
  - Next important event.
- Voice commands:
  - “Jarvis, what’s on my schedule today?”
  - “Do I have anything tomorrow morning?”
- Output:
  - Spoken summary.
  - Vault file:
    - `calendar/YYYY-MM-DD/HHMM_briefing.md`.

---

## 11. PERFORMANCE & OPTIMISATION

### 11.1 TTS & WS Stability
- Continue tuning:
  - PCM chunk size.
  - Async yields.
  - Ping interval/timeouts.
- Add retry-on-close:
  - One quick reconnection attempt before dropping client.

### 11.2 LLM Latency
- Explore:
  - quantised models
  - caching JARVIS persona preamble
  - smaller context windows for short questions.
- Benchmark:
  - per-model average latency
  - CPU/GPU impact.

---

## 12. FUTURE / NICE-TO-HAVE

These are not required now but tracked for future phases:

- **Conversation Mode**:
  - temporary continuous listening mode when explicitly enabled.
- **Stress / Mood Detection**:
  - detect vocal stress markers.
- **Home Assistant Integration**:
  - once camera/privacy approach is stable.
- **Gesture Controls** (if PTZ Insta360 chosen).
- **Remote Access**:
  - secure tunnel for off-site management.

---

# END OF TODO FILE
