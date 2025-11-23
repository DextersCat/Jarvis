# JARVIS STATE SNAPSHOT — 2025-11-18 16:45 SESSION CHECKPOINT

**Session Status**: Performance degrading, checkpoint before break
**System State**: Mode B ready (PC Brain running, AI-Pi client configured)
**Next Action**: Execute `~/Desktop/start-jarvis-client.sh` on AI-Pi to connect

---

## High-Level

- Goal: Ultimate Jarvis / AI-Pi setup.
- AI-Pi = always-on ears + voice (Mode A solo, Mode B distributed).
- PC + GPU = optional super-brain for heavy tasks (Whisper, GPT, docs, RACI).
- F: = Jarvis models + vault island.
- E: = Personal / games – **off-limits** to Jarvis.

## Current Architecture Status

### PC Brain (WSL / GPU)

- Jarvis Brain server **ONLINE**.
- Log confirms:
  - faster-whisper `medium.en` loaded on **CUDA**, `float16`.
  - WebSocket server listening on `ws://0.0.0.0:8765`.
  - Audio format: 16000 Hz, 1ch, 16-bit PCM.
  - Waiting for AI-Pi connections.
- Runtime log example:
  - `/root/JARVIS/runtime/logs/phase_c3_server_20251118_*.log`

### Windows Control Plane

- Main workspace: `C:\Users\spenc\JARVIS-Workspace\`
- Key folders:
  - `api\` — includes `server.py` etc.
  - `core\` — Jarvis brain, personality, engines.
  - `temp_ai_pi_modules\` — AI-Pi client modules (recorder, playback, VAD, client).
  - `ARCHITECTURE-DISTRIBUTED-JARVIS.md`
  - `WORKSPACE-DIRECTORY-GUIDE.md`
  - `PREFERENCES.md`
- Status:
  - G1–G4 tests: ✅ passed.
  - PC-side Jarvis Core logic is healthy.

### Storage Layout (Windows)

- `C:\Users\spenc\JARVIS-Workspace\` → code, configs, logs, docs.
- `F:\JARVIS_MODELS\` → created; target for Whisper/TTS/embeddings/LLM models.
- `F:\JARVIS_VAULT\` → created; target for long-term Jarvis data.
- `E:\` → **personal only**, never used by Jarvis.

### AI-Pi (Edge Node)

- Project root: `~/jarvis_terminal/`

**TWO SEPARATE VOICE SYSTEMS:**

1. **DISTRIBUTED SYSTEM (Phase C3) - PRIMARY ARCHITECTURE:**
   - `client.py` + `recorder.py` + `playback.py` + `vad.py` + `hotword.py`
   - Flow: Wake word → Record with VAD → Stream PCM to PC Brain (WebSocket) → faster-whisper GPU → Brain → TTS → Stream back → Play
   - **STATUS:** ✅ TESTED TODAY - This is how you found the time bug
   - Uses PC Brain WebSocket (ws://192.168.1.26:8765)
   - GPU-accelerated Whisper (faster-whisper, CUDA, medium.en)
   - All modules deployed in `temp_ai_pi_modules/` on Windows workspace

2. **STANDALONE SYSTEM (Phase G5) - FALLBACK/TESTING:**
   - `voice_session.py` (395 lines)
   - Flow: Mic → OpenAI Whisper API → GPT → OpenAI TTS API → ffplay
   - **STATUS:** ✅ Works but uses cloud APIs (not GPU, slower, costs money)
   - Used for standalone testing when PC Brain offline
   - Test: "Jarvis, give me a system state summary?" (worked with US voice)

- Files:
  - `~/jarvis_files/` exists.
  - `delivery_team_raci_seed.txt` present (VAYRO Delivery Team RACI seed).
  - Desktop symlink "Jarvis Files" → `~/jarvis_files/`.
- Mode B deployment status:
  - PC brain is ready and listening (ws://0.0.0.0:8765).
  - AI-Pi client modules tested and working (client.py + audio modules).
  - persistent_client.py created to ADD always-on service + REST API capability.

## Phase / Work Plan

### Completed

- G1–G4: Core logic & safety tests ✅
- G5: AI-Pi standalone voice loop ✅
- C3 (Brain server): PC Brain on GPU online, listening on 8765 ✅
- F: drive:
  - `F:\JARVIS_MODELS\` and `F:\JARVIS_VAULT\` created and documented ✅
- Clean-desk docs:
  - `ARCHITECTURE-DISTRIBUTED-JARVIS.md` updated with dual-mode vision.
  - `WORKSPACE-DIRECTORY-GUIDE.md` updated with Windows storage map.
  - `PREFERENCES.md` updated with model storage rules and E:\ restriction.

### In Progress / Pending

- Mode B distributed voice (client.py + recorder + playback + vad):
  - ✅ TESTED TODAY via client.py + audio modules → PC Brain WebSocket
  - ⏳ Integration with persistent_client.py (add always-on + REST API)
  - ⏳ Deploy integrated system to AI-Pi for 24/7 operation
- Phase A timings:
  - Three test phrases (via integrated persistent_client.py + audio modules):
    1. "Jarvis, what's the time?"
    2. "Jarvis, give a system summary?"
    3. "Jarvis, can you access the Vayro team RACI document?"
- Phase G6:
  - Persona & voice tuning:
    - British Jarvis style.
    - Calls user “Sir” by default; “Dex” reserved for friendly moments.
- Phase G7:
  - Google/Gmail integration re-link (Calendar + email access) for work support.
- Phase G8:
  - RACI pipeline for VAYRO (Enterprise RACI, Project YETI RACI, Delivery Team RACI).
  - Jarvis must be able to read seed files and generate/update RACIs.

## Session Checkpoint Notes (16:45)

### Ready State Summary
- **PC Brain Server**: RUNNING since 16:19, port 8765, log `/root/JARVIS/runtime/logs/phase_c3_server_20251118_161859.log`
- **AI-Pi Client**: CONFIGURED, .env has PC IP (192.168.1.26), all files present
- **Desktop Shortcut**: `~/Desktop/start-jarvis-client.sh` created at 16:42
- **Network**: Verified - port 8765 accessible from AI-Pi to PC
- **Status**: System at "magic moment" - one click from Mode B connection

### Next Session Protocol
1. Read `WORKSPACE-DIRECTORY-GUIDE.md` (system recovery)
2. Read `PREFERENCES.md` (rules and preferences)
3. Verify PC Brain Server running: `./launch-ubuntu-jarvis.ps1` if needed
4. Execute on AI-Pi: `~/Desktop/start-jarvis-client.sh` (or via SSH)
5. Verify connection in PC Brain Server logs
6. Run three-test timing analysis
7. Report to user and Astra

### Critical Lessons From This Session
- Agent made false blocker about Ubuntu paths (assumed didn't exist without checking)
- Session length (20+ hours) caused performance degradation
- Documentation MUST be updated in real-time, not at session end
- Never assume infrastructure doesn't exist - always verify first
- Long sessions risk crash - checkpoint and break when performance degrades

## Golden Rules (Runtime)

- Nexus and any tools must:
  - Read `WORKSPACE-DIRECTORY-GUIDE.md` and `PREFERENCES.md` at session start.
  - Never modify E:\.
  - Store heavy models only under `F:\JARVIS_MODELS\`.
  - Use only Mode A (AI-Pi solo) or Mode B (PC brain) as documented.
  - Never invent a third architecture or new random paths.
- AI-Pi must always remain usable in Mode A even if PC is off.
- PC Brain is an optional performance/feature upgrade, not a hard dependency.
