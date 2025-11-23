# JARVIS STATE MASTER (as of 2025-11-21)

This document acts as the authoritative high-level reference for the entire Jarvis system across both Ai-Pi and the PC Brain. It summarises capabilities, architecture, dependencies, and behavioural rules in a single consolidated master file.

---

# 1. CORE VISION

Jarvis is not a chatbot.
It is a **device**, with predictable behaviour, stable modes, and a defined personality.

The architecture is hybrid:

- **Ai-Pi** = body  
- **PC Brain** = mind  
- **Vault (F:\JARVIS_VAULT)** = long-term memory  
- **HUD** = face  
- **Astra** = CTO and governance layer  

Jarvis must be:
- stable  
- recoverable  
- offline-capable  
- deterministic  
- fast  
- safe  
- extensible  

---

# 2. SYSTEM COMPONENTS

## Ai-Pi (Body)
- Wake word via Porcupine (“Jarvis”)
- Local Whisper Tiny STT
- Local intent handling (time/date)
- Speech → text → queue if offline
- Plays TTS audio and voice assets
- React HUD running on localhost:5000
- REST API on 8766
- Health checks and event logs
- Queue handling (add/remove/flush)
- Modes:
  - Normal
  - Gaming (wake disabled)
  - Shutdown (clean exit)
  - Initialize (health summary)

## PC Brain (Mind)
- WebSocket server on 8765
- LLaMA3 via Ollama (local reasoning)
- Memory engine with embeddings
- Personality preference injection
- FileService writes to F:\
- TTS: OpenAI Fable
- Structured logs and traceability
- Planned:
  - Email (BT Mail + Gmail API)
  - Calendar (Google Calendar)
  - Web search (Google Programmable Search)
  - Multi-model selection (ModelManager)
  - Scene/presence detection (camera)

---

# 3. DATA & STORAGE

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
Everything written by the Brain must go here:
- System checks
- Notes
- Observations
- Dev/test files
- Web summaries
- Calendar/email outputs

This directory is:
- versioned
- human-readable
- AI-readable
- backed up
- expandable to 4TB+

---

# 4. COMMUNICATION FLOW

### Online state:
1. Wake → STT  
2. Text forwarded to Brain  
3. Brain → LLM → TTS  
4. Ai-Pi plays audio response  

### Offline state:
1. Wake → STT  
2. Ai-Pi detects Brain offline  
3. Plays offline asset  
4. Adds text to queue  
5. HUD updates queue count  

---

# 5. MODES & BEHAVIOUR

### Normal Mode
- Wake word enabled  
- STT active  
- Brain expected online  
- Queue flushed when Brain returns  

### Gaming Mode
- Wake word disabled  
- HUD indicator ON  
- STT off  
- Prevents accidental triggers  

### Shutdown Mode
- Clean stop of Pi processes  
- LXTerminal remains open  
- HUD shuts down gracefully  

### Offline Mode
- Offloaded to queue  
- Audio cue plays  
- HUD updates queue list  

---

# 6. GOVERNANCE RULES

Astra = CTO  
Sir = Owner/Director  
Nexus/Codex = Engineers  
Teddy = QA  
Dragons = Vault guardians  

Governance:
- No guessing  
- No unsafe refactors  
- No installing anything without approval  
- Research → Propose → Test → Verify  
- Logs tell the truth  
- HUD and Vault must always remain consistent  
- All code changes must be reversible  

---

# 7. CURRENT CAPABILITIES (21 NOV 2025)

### ✓ Stable Pi wake-word  
### ✓ Stable Pi STT  
### ✓ Stable Brain LLM pipeline  
### ✓ TTS fixed  
### ✓ Structured file writing  
### ✓ Memory V1+V2 hybrid  
### ✓ Queue handling  
### ✓ HUD controls operational  
### ✓ System checks saved to Vault  
### ✓ Dev test-file creation  

---

# 8. ACTIVE WORKSTREAMS

### HIGH PRIORITY
- Long-form STT  
- Email & calendar  
- Web search  
- Voice asset expansion  
- Presence/camera detection  
- Wake-word tuning  
- HUD redesign  
- Model Manager  

### MEDIUM PRIORITY
- Stress detection (voice)  
- Conversation mode  
- Wake-word replacement options  
- Adaptive TTS speed  

---

# 9. HARDWARE MAP

### Ai-Pi:
- Raspberry Pi 5 (8GB)
- Whisper Tiny STT
- Porcupine wake word
- Onboard microphone (replaced soon)
- Elgato Wave:3 arriving Monday
- Camera optional (pending upgrade)

### Brain PC:
- 2TB NVMe  
- Another 2TB arriving  
- Ollama engine  
- Waveform displays  
- CPU/RAM temp monitoring  
- OpenAI TTS (cloud)  

---

# 10. LONG-TERM VISION

Jarvis becomes:
- your personal AI butler  
- aware of presence  
- aware of schedule  
- aware of environment  
- configurable with personas  
- stable to keep running 24/7  
- private (local reasoning first)  
- cloud-assisted where beneficial  

---

# END OF MASTER FILE
