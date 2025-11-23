# JARVIS Workspace Directory Structure
**Date:** November 18, 2025 16:20  
**Purpose:** Reference guide for Nexus and all AI agents to recover system knowledge  
**Status:** Living document - update IMMEDIATELY after verifying changes  
**Last Verified State:** 2025-11-18 16:19 - PC Brain Server RUNNING

---

## ⚠️ MANDATORY FOR ALL AI AGENTS

**IF CHAT CRASHES - READ THIS FIRST:**
This document contains verified working states with timestamps. Trust these verified checkpoints to resume work without re-testing everything.

---

## 🎯 Purpose

This document serves as a **memory anchor** for AI agents across sessions. If chat context is lost or a new session begins, agents should read this file FIRST to understand:
- Current system architecture
- File locations
- Active projects and phases
- Configuration details
- Known issues and workarounds

---

## 🗺️ Windows Storage Map

**C:\ Drive - Code & Configuration:**
```
C:\Users\spenc\JARVIS-Workspace\
├── Code files (*.py, *.ps1)
├── Configuration files (*.json, *.env)
├── Logs and runtime data
└── Documentation (docs/)
```

**F:\ Drive - Jarvis AI Island (Dedicated):**
```
F:\JARVIS_MODELS\
├── Whisper models (speech-to-text)
├── TTS models (text-to-speech)
├── Embedding models (semantic search)
└── Other heavy AI models

F:\JARVIS_VAULT\
├── Long-term Jarvis data
├── Document archives
├── Conversation backups
└── Historical knowledge base
```

**E:\ Drive - PERSONAL (OFF-LIMITS):**
- E:\ is explicitly marked as personal storage
- Jarvis must **NEVER** use E:\ for anything
- No reads, writes, or references to E:\ allowed

---

## 📁 Root Directory Structure

```
C:\Users\spenc\JARVIS-Workspace\
├── README.md                          # Main workspace overview
├── docs\                              # 📚 ALL DOCUMENTATION (organized)
│   ├── ARCHITECTURE-DISTRIBUTED-JARVIS.md  # PC Brain + AI-Pi architecture
│   ├── PHASE-G-SUMMARY.md            # Phase G completion report
│   ├── PHASE-G5-VOICE-COMPLETE.md    # G5 Voice Mode documentation
│   ├── ASTRA-NEXT-STAGE.md           # Astra AI handoff notes
│   ├── PHASE_C3_INTEGRATION.md       # WebSocket integration guide
│   ├── PHASE_C3_COMPLETE.md          # Phase C3 completion
│   ├── PHASE_C3_SUMMARY_FOR_ASTRA.md # C3 summary
│   ├── PHASE_C4_OPTIMISATION.md      # C4 optimization notes
│   ├── PHASE-E-COMPLETE.md           # Phase E summary
│   ├── PHASE-F-STATUS.md             # Phase F status
│   ├── AI-PI-CONFIG-GUIDE.md         # AI-Pi configuration
│   ├── AQARA-SETUP-GUIDE.md          # Aqara hub setup
│   ├── SETUP-REPORT.md               # Initial setup
│   └── quick-commands.md             # Quick reference commands
│
├── api\                              # 🌐 WebSocket Server (PC Brain)
│   ├── server.py                     # Main WebSocket server (383 lines)
│   └── README.md
│
├── ⚠️ NOTE: core\ brain components are in WSL2 at ~/JARVIS/core/, NOT in Windows workspace
│   # See "WSL2 Ubuntu Brain Structure" section below for actual location
│
├── temp_ai_pi_modules\               # 🎙️ AI-Pi Client Code (to be deployed)
│   ├── client.py                     # WebSocket client (341 lines)
│   ├── hotword.py                    # Wake word detection
│   ├── recorder.py                   # Microphone recording
│   ├── playback.py                   # Audio playback
│   ├── vad.py                        # Voice activity detection
│   └── vad_optimized.py              # Optimized VAD
│
├── config\                           # ⚙️ Configuration Files
│   └── README.md
│
├── ai-pi-backups\                    # 💾 AI-Pi Backup Files
│   ├── RESTORE-GUIDE.md              # Restore instructions
│   └── restore-jarvis.sh             # Restore script
│
├── models\                           # 🤖 AI Model References
│   └── README.md
│
├── multimodal\                       # 🎨 Multimodal AI Components
│   └── README.md
│
├── runtime\                          # 🏃 Runtime Files
│   └── README.md
│
├── speech\                           # 🗣️ Speech Processing
│   └── README.md
│
├── tests\                            # 🧪 Test Files
│   └── README.md
│
├── PowerShell Scripts (root level)   # 🚀 Launchers & Tools
│   ├── launch-ubuntu-jarvis.ps1      # Start PC Brain server
│   ├── launch-ai-pi.ps1              # Connect to AI-Pi
│   ├── launch-both.ps1               # Launch both systems
│   └── configure-c3-network.ps1      # Network configuration
│
└── Python Files (root level)         # 🐍 Legacy/Standalone Scripts
    ├── action_engine.py              # Action orchestration
    ├── calendar_service.py           # Google Calendar integration
    ├── email_service.py              # Gmail integration
    ├── memory_engine.py              # Memory system (legacy)
    ├── planning_engine.py            # Planning engine
    ├── prompt_engine.py              # Prompt management
    ├── task_engine.py                # Task execution
    ├── vault_engine.py               # Document vault
    ├── phase_d_config.py             # Phase D configuration
    ├── phase_d_demo.py               # Phase D demo
    └── test_*.py                     # Various test scripts
```

---

## 🎙️ AI-Pi Directory Structure

```
/home/spencer/jarvis_terminal/        # Main JARVIS installation
├── voice_session.py                  # Phase G5 Voice Mode (395 lines)
├── action_engine.py                  # Action orchestration (13,971 bytes)
├── memory_engine.py                  # Memory system (320 lines)
├── task_engine.py                    # Task execution (600+ lines)
├── planning_engine.py                # Planning engine (370 lines)
├── vault_engine.py                   # Document vault (500+ lines)
├── email_service.py                  # Gmail integration
├── calendar_service.py               # Google Calendar integration
├── prompt_engine.py                  # Prompt management
├── core/                             # Core configuration
│   ├── __init__.py
│   └── config.py                     # Configuration constants
├── logs/                             # Log files
│   └── g5_voice_sessions.log         # Voice session logs
├── audio/                            # Audio processing
├── config/                           # Configuration files
│   └── .env                          # Environment variables
├── networking/                       # Network modules
├── runtime/                          # Runtime files
└── tests/                            # Test scripts
    ├── test_g1_planning.py           # Planning engine tests
    ├── test_g2_memory.py             # Memory engine tests
    ├── test_g3_vault.py              # Vault engine tests
    └── test_g4_tasks.py              # Task engine tests (VERIFIED WORKING)

/home/spencer/jarvis_terminal_env/    # Python virtual environment (1.4GB)
├── bin/activate                      # Activate script (REQUIRED)
└── lib/python3.13/site-packages/     # 122 packages

/home/spencer/jarvis_memory/          # ChromaDB storage (852KB)
├── 7 collections (29 items total)
│   ├── preferences (1 item)          # User preferences
│   ├── conversations (20 items)      # Conversation history
│   ├── people (0 items)
│   ├── projects (0 items)
│   ├── routines (0 items)
│   ├── systems (7 items)
│   └── knowledge (0 items)

/home/spencer/jarvis_files/           # User files
├── delivery_team_raci_seed.txt      # VAYRO team RACI document
└── (future files)

/home/spencer/Desktop/                # Desktop shortcuts
└── Jarvis Files -> /home/spencer/jarvis_files

/data/Jarvis_Vault/                   # Document vault (568KB, 652GB available)
├── documents/                        # Ingested documents
├── tasks/                            # Task storage
├── vault_db/                         # Vault ChromaDB index
└── g5_prep/                          # G5 preparation files

/home/spencer/.jarvis_tokens/         # API credentials
└── .env                              # OpenAI API key, etc.
```

---

## 🔑 Critical File Locations

### Configuration Files
- **PC:** `C:\Users\spenc\JARVIS-Workspace\phase_d_config.py`
- **AI-Pi:** `/home/spencer/jarvis_terminal/core/config.py`
- **AI-Pi Env:** `/home/spencer/.jarvis_tokens/.env`

### Credentials
- **Google OAuth:** `calendar_token.json`, `gmail_token.json` (location TBD)
- **OpenAI API:** In `.env` files

### Entry Points
- **PC Brain:** `api/server.py` (WebSocket server)
- **AI-Pi Voice:** `~/jarvis_terminal/voice_session.py` (standalone mode)
- **AI-Pi Client:** `temp_ai_pi_modules/client.py` (distributed mode)

### Launch Scripts
- **PC Brain:** `launch-ubuntu-jarvis.ps1`
- **AI-Pi SSH:** `launch-ai-pi.ps1`
- **Both Systems:** `launch-both.ps1`

---

## 📊 Current System Status

### Phase Completion
- ✅ **Phase G1:** Planning Engine (ALL TESTS PASSED)
- ✅ **Phase G2:** Memory Engine (ALL TESTS PASSED)
- ✅ **Phase G3:** Knowledge Vault (ALL TESTS PASSED)
- ✅ **Phase G4:** Task Engine (ALL TESTS PASSED - verified 2025-11-18)
- ✅ **Phase G5:** Voice Mode Stage 1 & 2 (COMPLETE)
  - Stage 1: Mic → Whisper → Jarvis → Text ✅
  - Stage 2: Text → TTS → Audio Output ✅

### Active Architecture
**Current:** Standalone AI-Pi (Phase G5)
- File: `~/jarvis_terminal/voice_session.py`
- Mode: All processing on AI-Pi
- Dependencies: OpenAI Whisper API, GPT-4o-mini, TTS API

**Available:** Distributed PC Brain + AI-Pi (Phase C3)
- PC: `api/server.py` (WebSocket server)
- AI-Pi: `temp_ai_pi_modules/client.py`
- Mode: AI-Pi audio I/O, PC brain processing
- Status: Code exists but not currently deployed

### Known Issues
1. **Memory Recall Warning:** `action_engine.py` expects `memory_engine.recall()` method
   - Impact: Log warning but non-breaking
   - Status: Not yet fixed
2. **OAuth Tokens:** Gmail and Calendar tokens not configured
   - Impact: Email/calendar features unavailable
   - Status: Pending OAuth flow
3. **Import Structure:** Some files use `from core.*` imports
   - Fixed by creating `~/jarvis_terminal/core/` package
   - Status: Resolved

---

## 🔧 System Requirements

### AI-Pi (Raspberry Pi 5)
- **OS:** Raspberry Pi OS Desktop (Debian 13 trixie)
- **Kernel:** 6.12.47+rpt-rpi-2712
- **Python:** 3.13.5 (system) + venv
- **Storage:** 1TB NVMe (boot), 128GB NVMe (data)
- **Audio:** USB 2.0 Camera mic, HDMI monitor speakers
- **Network:** WiFi/Ethernet, SSH enabled (spencer@ai-pi.local)

### PC (Windows)
- **OS:** Windows 11 (with WSL2)
- **WSL:** Ubuntu 22.04 LTS
- **Python:** 3.10.12 (in `~/jarvis_env`)
- **GPU:** NVIDIA RTX 5070 Ti (16GB VRAM)
- **CUDA:** 13.0 (via Windows driver)
- **Network:** Port 8765 forwarded to WSL2

---

## 🚀 Quick Start Commands

### AI-Pi Voice Mode (Standalone)
```bash
ssh -t spencer@ai-pi.local 'cd ~/jarvis_terminal && source ~/jarvis_terminal_env/bin/activate && python3 voice_session.py'
```

### Test AI-Pi Components
```bash
# Test Task Engine (most recent)
ssh spencer@ai-pi.local 'cd ~/jarvis_terminal && source ~/jarvis_terminal_env/bin/activate && python3 test_g4_tasks.py'

# Test Memory Engine
ssh spencer@ai-pi.local 'cd ~/jarvis_terminal && source ~/jarvis_terminal_env/bin/activate && python3 test_g2_memory.py'

# Test Planning Engine
ssh spencer@ai-pi.local 'cd ~/jarvis_terminal && source ~/jarvis_terminal_env/bin/activate && python3 test_g1_planning.py'

# Test Vault Engine
ssh spencer@ai-pi.local 'cd ~/jarvis_terminal && source ~/jarvis_terminal_env/bin/activate && python3 test_g3_vault.py'
```

### PC Brain Server
```powershell
# Launch PC Brain (Ubuntu WSL2)
.\launch-ubuntu-jarvis.ps1

# Configure network (first time)
.\configure-c3-network.ps1
```

---

## 📝 Important Notes for AI Agents

### Always Remember
1. **ALWAYS activate venv on AI-Pi:** `source ~/jarvis_terminal_env/bin/activate`
2. **Import pattern:** `sys.path.insert(0, '/home/spencer/jarvis_terminal')` then direct imports
3. **Test files are canonical:** Use `test_g4_tasks.py` as reference (most recent, verified working)
4. **Read this file first:** If context is lost, read this document to recover system knowledge
5. **Update this file:** After major changes, update this document

### File Organization Rules
1. **Documentation:** ALL `.md` files go in `docs/` folder (except `README.md`)
2. **Code:** Keep Python files at root or in appropriate subdirectories
3. **Tests:** Keep test files together (AI-Pi: `tests/`, PC: `tests/`)
4. **Configs:** Keep configuration files in `config/` or `core/`
5. **⚠️ CRITICAL:** PC Brain core files live in WSL2 at `/root/JARVIS/core/`, NOT in Windows workspace. Never create duplicate `core/` in Windows workspace.

### Debugging Pattern
1. Check if venv is activated
2. Verify import paths (`sys.path.insert`)
3. Check for missing packages (`pip list`)
4. Review test files for correct patterns
5. Check logs: `~/jarvis_terminal/logs/`

---

## 🔄 Version Control

### Last Major Changes
- **2025-11-18:** Phase G5 Voice Mode complete (TTS added)
- **2025-11-18:** File organization (docs/ folder created)
- **2025-11-18:** Distributed architecture documented
- **2025-11-17:** Phase G (G1-G4) engines complete
- **2025-11-16:** AI-Pi case rebuild and restore

### Next Planned Changes
- Phase G6: Wake word detection
- Phase G7: Proactive intelligence
- ~~Decision: Migrate to distributed architecture (C3)?~~ **RESOLVED: Distributed (Mode B) is deployed and working on Ubuntu WSL2**

---

## ⚠️ CRITICAL LESSONS FROM SESSION CRASHES

### 2025-11-18 Session Recovery Notes
**What Happened:** 9-hour data loss due to chat crash without proper documentation

**Prevention Measures:**
1. **ALWAYS update WORKSPACE-DIRECTORY-GUIDE.md immediately** after confirming any system works
2. **NEVER assume infrastructure doesn't exist** - verify first by running/checking
3. **Document verified working states** - not just plans or theories
4. **Update docs BEFORE moving to next task** - not at end of session

**Verified Working Systems (2025-11-18 16:19):**
- ✅ PC Brain Server: Ubuntu WSL2 `~/JARVIS/api/websocket_server/server.py` RUNNING on port 8765
- ✅ GPU Whisper: NVIDIA RTX 5070 Ti, CUDA, float16, medium.en model ACTIVE
- ✅ Personality Framework: PersonalityEngine, ContextManager, ProactiveSuggestionEngine LOADED
- ✅ JARVISMemory: 4 conversations in ChromaDB ACTIVE
- ✅ Launch Script: `.\launch-ubuntu-jarvis.ps1` WORKS PERFECTLY

**Still Needed:**
- ⏸️ AI-Pi client deployment from `temp_ai_pi_modules/` to AI-Pi
- ⏸️ Client configuration with PC IP address
- ⏸️ Mode B end-to-end testing

---

**Status:** Living document - Update after significant changes  
**Last Updated:** November 18, 2025 16:20 (POST-CRASH RECOVERY UPDATE)  
**Maintained By:** Nexus (AI agent) + Spencer (Chairman)
