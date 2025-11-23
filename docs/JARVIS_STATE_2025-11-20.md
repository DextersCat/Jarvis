# JARVIS SYSTEM STATE — 2025-11-20

**Mode:** Hybrid Local Assistant  
**Hardware:**  
- Ai-Pi: Raspberry Pi 5 (Jarvis “Body”)  
- PC: Windows 11 + WSL2 Ubuntu (Jarvis “Brain”)  
- GPU: RTX (used by Whisper + LLaMA3 via Ollama)

---

## 1. High-Level Architecture

Jarvis is now a **two-part system**:

- **Ai-Pi (“Body”)**  
  - Wake word + PTT  
  - Local STT (Whisper Tiny)  
  - Simple local intents (time/date)  
  - Queue + offline handling  
  - REST API for HUD  
- **PC (“Brain”)**  
  - JARVISBrain: LLaMA3 + rich personality, memory, context  
  - Fable TTS via OpenAI  
  - WebSocket server for Pi  
- **HUDs**  
  - Web HUD on Pi (React + Express)  
  - Brain HUD on PC (Tkinter buttons & logs)

---

## 2. Ai-Pi Layer — `jarvis_lite.py`

Responsibilities include wake word detection, local STT, handling local intents, queueing, and REST API for HUD.

---

## 3. PC Brain Layer — `server.py` + `jarvis_brain.py`

Handles WebSocket bridging, LLM reasoning via Ollama LLaMA3, and Fable TTS generation.

---

## 4. Brain HUD — `brain_hud.py`

Tkinter GUI to control neural net initialization, shutdown, and gaming mode.

---

## 5. Calendar & Email Modules

`calendar_service.py` and `email_service.py` are implemented but not yet integrated.

---

## 6. Startup Procedure (Manual)

Outlines how to manually start the Brain HUD, server, Pi backend, and HUD.

---

## 7. Known Gaps & Next Goals

Includes creation of a simple Pi start script, wiring calendar/email, and future enhancements.

---

## 8. Summary

You currently have a working hybrid Jarvis with clear modules and next steps.
