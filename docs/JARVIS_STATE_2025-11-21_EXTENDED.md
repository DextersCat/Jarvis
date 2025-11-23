# JARVIS STATE — EXTENDED (2025-11-21)

This document consolidates the complete JARVIS system state as of 21 November 2025, incorporating all upgrades, behaviours, subsystems, and architectural decisions made up to this point.

---

# 1. SYSTEM ARCHITECTURE OVERVIEW

## Ai-Pi (BODY)
- Runs `jarvis_lite.py`
- Wake word: Porcupine (“Jarvis”)
- Whisper Tiny STT (local)
- Local intents (time/date)
- Offline queue (queue.json)
- Audio asset playback (mp3)
- REST API on port 8766
- HUD (React + Express) on port 5000
- Event logging + state reporting
- Gaming mode (wake word suspended)
- Shutdown mode (clean process exit)
- Initialize mode (health summary)

## PC Brain (MIND)
- WebSocket server on port 8765
- `jarvis_brain.py` + `server.py`
- LLaMA3 via Ollama (`http://localhost:11434`)
- Context manager + memory retrieval
- Memory DB (vector storage)
- FileService → writes to Vault on F:
- Structured notes, system checks, observations
- TTS via OpenAI **Fable**
- Planned modules:
  - Email service (BT Mail, Gmail fallback)
  - Calendar service (daily briefings)
  - Web Search (Google Programmable Search)
  - ModelManager (multi-model selection)

---

# 2. BRAIN SUBSYSTEMS

## MEMORY ENGINE
- Conversation memory stored per turn
- Query → retrieve → embed → store
- Personality preferences injected
- Memory types:
  - Observations
  - Notes
  - Timestamped logs
  - System-level events
- Planned: category tagging (Teddy, Social, Health)

## FILESERVICE (FULLY IMPLEMENTED)
- Safe writing under:
  `F:\JARVIS_VAULT\YYYY\MM\DD\...`
- Sanitised filenames
- Timestamp fallback to avoid overwrites
- Subfolders:
  - system
  - notes
  - dev
  - teddy
  - web
- Tested:
  - System checks
  - Dev file creation
  - Notes/observations

## DEV TEST-FILE COMMAND
Trigger phrases:
- “Create me a test file called X”
- “Jarvis, create a file called X”

Creates markdown files under:
`F:\JARVIS_VAULT\YYYY\MM\DD\dev\`

## TTS PIPELINE (STABLE)
- MP3 → PCM converter
- Chunked PCM streaming
- Yielding async loop to avoid ping timeouts
- Fixed “no close frame received” errors
- Improved persistence for long replies

---

# 3. Ai-Pi SUBSYSTEMS

## HUD CONTROLS
- Initialize → health summary + API status
- Gaming mode → wake-word pause/resume
- Shutdown → clean exit, return to LXTerminal
- Queue display (live)
- Queue purge (single/all)

## QUEUE SYSTEM
- queue.json on Pi SSD
- Offline logic:
  - If wake word triggers and Brain is offline →
    - Play offline.mp3
    - Save text to queue
    - HUD updates queue count
- Online logic:
  - Pi forwards STT text → Brain
  - Brain processes and responds
  - Queue flush planned

## AUDIO ASSETS (CURRENT + PLANNED)
Current:
- offline.mp3

Planned:
- queue_purged.mp3
- queue_added.mp3
- gaming_on.mp3 / gaming_off.mp3
- shutdown.mp3
- greeting.mp3
- error_generic.mp3
- understood.mp3
- processing.mp3

## LONG-FORM STT (PLANNED)
- Increase utterance time window
- Improve VAD thresholds
- Allow 15–20 second instructions

---

# 4. VAULT LAYOUT (WINDOWS F:)

## Vault (Windows F:)
- Root: `F:\JARVIS_VAULT\`
- Subfolders by date: `YYYY\MM\DD\` 
- Sanitised filenames with timestamps
- Categories:
  - system
  - notes
  - dev
  - teddy
  - web\
- Vector DB for memory embeddings
- Structured logs and observations
- Safe write operations with overwrite prevention
- Future: category tagging for memories
---

# 5. SECURITY / CONFIG

## API KEYS
- Ai-Pi: stored in `~/.env`
- Brain: stored in `~/JARVIS/config/.env`

## NETWORK
- Brain reachable at static local IP
- Offline logic triggers queue
- LAN-only, no external exposure

---

# 6. TODO SUMMARY (MERGED)
*(Full TODO file will follow separately)*

- Long-form STT
- ModelManager
- Google Search
- Email service
- Calendar service
- Presence detection (camera)
- Nightly Astra check
- HUD redesign
- Conversation mode
- Wake-word sensitivity tuning
- System optimisation

---

# 7. KNOWN ISSUES (partial)
- TTS can still disconnect on extremely large replies
- Offline asset triggers too easily (fix planned)
- Presence detection pending new camera/mic
- HUD scaling improvements pending

---

# 8. HARDWARE NOTES
- **Elgato Wave:3** arriving Monday
- Considering **Insta360 Link 2**
- Additional 2TB SSD arriving
- PC running cool under load

---

# 9. GOVERNANCE (Roles)
- **Astra** = CTO/strategist  
- **Sir (you)** = Director/Owner  
- **Nexus/Codex** = Engineers  
- **Teddy** = QA Lead  
- **Dragons** = Vault Guardians  

Golden rules:
- No unsafe refactors
- No guessing
- One-path architecture
- Research → Propose → Test → Verify

---

# END OF FILE
