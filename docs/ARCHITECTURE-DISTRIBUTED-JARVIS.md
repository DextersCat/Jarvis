# JARVIS Distributed Architecture Documentation
**Date:** November 18, 2025  
**Author:** Nexus  
**Status:** Active Architecture (Phase C3 Design)

---

## 🎯 JARVIS Dual-Mode Runtime & Long-Term Vision

JARVIS supports **two operational modes**:

### Mode A - AI-Pi Solo (G5)
AI-Pi runs `voice_session.py` standalone for always-on ears/voice when PC is off.
- Uses OpenAI APIs (Whisper, GPT-4o-mini, TTS)
- Fully self-contained on Raspberry Pi 5
- Perfect for 24/7 voice assistant availability

### Mode B - Distributed (C3)
AI-Pi handles mic/speakers, PC runs the Jarvis Brain server over WebSocket port 8765.
- PC: `api/server.py` via `launch-ubuntu-jarvis.ps1`
- AI-Pi: `temp_ai_pi_modules/client.py` (WebSocket client)
- Faster local Whisper transcription (GPU-accelerated)
- Richer personality framework and proactive intelligence

### Storage Architecture
**F:\ drive is the dedicated island for Jarvis models and long-term data:**
- `F:\JARVIS_MODELS\` - Heavy AI models (Whisper, TTS, embeddings, etc.)
- `F:\JARVIS_VAULT\` - Long-term Jarvis data and archives
- `C:\Users\spenc\JARVIS-Workspace\` - Code, configs, and logs only

---

## 🎯 Overview

JARVIS operates as a **distributed AI system** with two primary components:

1. **PC Brain (Ubuntu WSL2)** - Core intelligence and processing
2. **AI-Pi Terminal (Raspberry Pi 5)** - Voice I/O interface

Communication occurs via **WebSocket protocol** on **port 8765**.

---

## 🖥️ PC Brain Server

### Location & Entrypoint
- **File:** `~/JARVIS/api/websocket_server/server.py` (Ubuntu WSL2) - ✅ VERIFIED WORKING 2025-11-18 16:19
- **Brain Core:** `~/JARVIS/core/jarvis_brain.py` (292 lines) - ✅ LOADED
- **Launch Script:** `.\launch-ubuntu-jarvis.ps1` (from Windows workspace) - ✅ TESTED

### Server Configuration
```python
Host: 0.0.0.0 (all interfaces)
Port: 8765 (default)
Protocol: WebSocket (JSON messages over UTF-8 text frames)
Environment Variables:
  - JARVIS_WS_HOST (default: '0.0.0.0')
  - JARVIS_WS_PORT (default: 8765)
```

### Verified Working State (2025-11-18 16:19)
```
Server starting on ws://0.0.0.0:8765
Whisper model loaded successfully
Whisper device: cuda, compute_type: float16
JARVIS BRAIN ONLINE - Ready for commands
server listening on 0.0.0.0:8765
Waiting for AI-Pi connections...
```

**Hardware Confirmed:**
- GPU: NVIDIA GeForce RTX 5070 Ti
- CPU: 16 cores
- RAM: 15.2 GB
- System: Ubuntu 22.04 WSL2 on SDMain

**Components Initialized:**
- ✅ OpenAI client
- ✅ PersonalityEngine (JARVIS British butler persona, 13 injection patterns)
- ✅ JARVISMemory (4 conversations, 0 preferences loaded)
- ✅ ContextManager (max_memories=3)
- ✅ ProactiveSuggestionEngine (3 rule patterns)
- ✅ faster-whisper (medium.en, GPU, CUDA, float16)

### Launch Command
```powershell
.\launch-ubuntu-jarvis.ps1
```

**Actual Execution:**
```bash
wsl -d Ubuntu-22.04 bash -c '
  export LD_LIBRARY_PATH=$HOME/jarvis_env/lib/python3.10/site-packages/nvidia/cudnn/lib:$LD_LIBRARY_PATH &&
  cd ~/JARVIS/api/websocket_server &&
  source ~/jarvis_env/bin/activate &&
  python3 server.py
'
```

### Core Components

**JARVISBrain Class** (`core/jarvis_brain.py`):
- Main intelligence engine
- OpenAI GPT-4o integration
- Personality framework integration
- System information gathering
- Session statistics tracking

**Personality Framework:**
- `PersonalityEngine` - JARVIS personality traits
- `ContextManager` - Conversation context management
- `ProactiveSuggestionEngine` - Proactive recommendations
- `JARVISMemory` - Long-term memory system

**Speech Processing:**
- **STT:** faster-whisper (medium.en model, CPU, int8)
  - Local GPU-accelerated transcription
  - Faster than cloud-based Whisper API
- **TTS:** OpenAI TTS API (tts-1 model)
  - Voice: "fable" (configurable)

### Processing Flow
```
AI-Pi Audio Stream (PCM 16kHz mono)
    ↓
WebSocket Server (port 8765)
    ↓
Audio Buffering (complete utterance)
    ↓
faster-whisper Transcription (GPU/CPU)
    ↓
JARVISBrain Processing
    ├─ Personality Engine
    ├─ Context Manager
    ├─ Proactive Engine
    └─ Memory System
    ↓
OpenAI GPT-4o Response Generation
    ↓
OpenAI TTS Audio Generation
    ↓
Base64 Encode + Stream to AI-Pi
    ↓
AI-Pi Playback (speakers)
```

---

## 🎙️ AI-Pi Terminal Client

### Location & Entrypoint
- **Client:** `temp_ai_pi_modules/client.py` (341 lines)
- **Supporting Modules:** `temp_ai_pi_modules/`
  - `hotword.py` - Wake word detection
  - `recorder.py` - Microphone recording
  - `playback.py` - TTS audio playback
  - `vad.py` / `vad_optimized.py` - Voice activity detection

### Client Configuration
```python
Connection URI: ws://{JARVIS_WS_HOST}:{JARVIS_WS_PORT}
Default: ws://localhost:8765
Environment Variables:
  - JARVIS_WS_HOST (default: 'localhost')
  - JARVIS_WS_PORT (default: 8765)
```

**For AI-Pi to connect to PC:**
- Set `JARVIS_WS_HOST` to PC's IP address on local network
- Port 8765 must be accessible (firewall configured)

### Client Classes

**JARVISWebSocketClient:**
- WebSocket connection management
- Reconnection with exponential backoff
- Message send/receive
- Ping/pong health checks
- Audio streaming to brain

**AudioStreamProtocol:**
- JSON message creation/parsing
- Base64 encoding/decoding
- Protocol message formatting

### Audio I/O Flow
```
Wake Word Detection ("Hey Jarvis")
    ↓
Microphone Recording (recorder.py)
    ↓
Voice Activity Detection (vad.py)
    ↓
WebSocket Client Connection
    ↓
Send: audio_start message
    ↓
Stream: audio_chunk messages (base64 PCM)
    ↓
Send: audio_end message
    ↓
Receive: tts_chunk messages
    ↓
Playback (playback.py via speakers)
    ↓
Receive: tts_end message
    ↓
Return to Wake Word Detection
```

---

## 📡 WebSocket Protocol

### Message Types

**Client → Server:**
```json
{"type": "ping"}
{"type": "audio_start"}
{"type": "audio_chunk", "data": "<base64_pcm_audio>"}
{"type": "audio_end"}
```

**Server → Client:**
```json
{"type": "pong"}
{"type": "ack", "message": "audio_start acknowledged"}
{"type": "tts_chunk", "data": "<base64_audio>"}
{"type": "tts_end"}
{"type": "error", "message": "error description"}
```

### Audio Format Specification
```
Sample Rate: 16000 Hz (16 kHz)
Channels: 1 (mono)
Sample Width: 16-bit (2 bytes per sample)
Encoding: PCM (Pulse Code Modulation)
Transmission: Base64-encoded chunks
Chunk Size: 4096 bytes (configurable)
```

---

## 🌐 Network Configuration

### Port Forwarding (Windows → WSL2)
**Script:** `configure-c3-network.ps1`

**Actions:**
1. Forward port 8765 from Windows to WSL2 IP
2. Create Windows Firewall rule for TCP 8765 inbound
3. Verify configuration

**Commands:**
```powershell
# Port forwarding
netsh interface portproxy add v4tov4 listenport=8765 listenaddress=0.0.0.0 connectport=8765 connectaddress={WSL_IP}

# Firewall rule
New-NetFirewallRule -DisplayName "JARVIS WebSocket" -Direction Inbound -LocalPort 8765 -Protocol TCP -Action Allow
```

### Network Topology
```
AI-Pi (192.168.x.x)
    ↓
    WiFi/Ethernet
    ↓
Windows PC (192.168.x.x)
    ↓
    Port 8765 (Firewall Allow)
    ↓
    Port Forwarding
    ↓
WSL2 Ubuntu ({dynamic_ip}:8765)
    ↓
JARVIS Brain Server
```

---

## 🔄 Current State vs. Original Architecture

### Phase G5 (Current - Standalone AI-Pi)
**Location:** AI-Pi only  
**File:** `~/jarvis_terminal/voice_session.py`

**Components:**
- Microphone input (sounddevice)
- OpenAI Whisper API (cloud transcription)
- Action Engine (local processing)
- OpenAI GPT-4o-mini (cloud)
- OpenAI TTS API (cloud)
- Speaker output (ffplay)

**Pros:**
- ✅ Standalone operation (no PC required)
- ✅ Simple architecture
- ✅ Easy to test and debug

**Cons:**
- ❌ Cloud API latency (Whisper, GPT, TTS)
- ❌ Limited processing power (Pi 5)
- ❌ No personality framework
- ❌ No proactive suggestions
- ❌ Higher API costs

### Phase C3 (Original - Distributed)
**Location:** PC Brain + AI-Pi Client

**PC Components:**
- faster-whisper (local GPU transcription)
- JARVISBrain (full intelligence)
- Personality framework
- Proactive engine
- OpenAI GPT-4o (cloud)
- OpenAI TTS (cloud)

**AI-Pi Components:**
- Wake word detection
- Microphone recording
- Voice activity detection
- Audio streaming
- TTS playback

**Pros:**
- ✅ Fast local Whisper (GPU-accelerated)
- ✅ Full personality framework
- ✅ Proactive suggestions
- ✅ Richer context management
- ✅ Better scalability

**Cons:**
- ❌ Requires PC to be running
- ❌ Network dependency
- ❌ More complex setup

---

## 📊 Performance Comparison

### Latency Estimates

**Standalone AI-Pi (Phase G5):**
```
Mic → Record → Whisper API → GPT API → TTS API → Speakers
      5s       1.5s          2s        1.5s       Local

Total: ~10 seconds per interaction
```

**Distributed (Phase C3):**
```
Mic → Stream → Local Whisper → Brain → TTS API → Stream → Speakers
      5s       0.5s            1s       1.5s       0.5s

Total: ~8.5 seconds per interaction
```

**Expected Improvements:**
- Whisper transcription: 1.5s → 0.5s (3x faster with GPU)
- Network overhead: +0.5s streaming
- Net improvement: ~1.5s reduction

---

## 🔧 Migration Path (G5 → C3)

### Option 1: Keep Both Architectures
- **Standalone Mode:** AI-Pi only (simple testing, demos)
- **Distributed Mode:** PC Brain + AI-Pi (production, full features)
- Switch via configuration/environment variables

### Option 2: Full Migration to C3
1. Start PC Brain server (`launch-ubuntu-jarvis.ps1`)
2. Configure AI-Pi client to connect to PC
3. Transfer AI-Pi modules (`temp_ai_pi_modules/` → AI-Pi)
4. Set environment variables on AI-Pi
5. Test connection (ping/pong)
6. Run full voice session

### Required Steps for Migration
1. **PC Side:**
   - Verify Ubuntu WSL2 environment (`~/jarvis_env`)
   - Install dependencies (websockets, faster-whisper, openai)
   - Configure `.env` file (OpenAI API key)
   - Run network configuration script
   - Launch server

2. **AI-Pi Side:**
   - Install client dependencies (websockets, pyaudio)
   - Copy `temp_ai_pi_modules/` to AI-Pi
   - Set `JARVIS_WS_HOST` to PC IP address
   - Test client connection
   - Integrate with wake word/VAD

3. **Network:**
   - Run `configure-c3-network.ps1` on Windows
   - Verify firewall allows port 8765
   - Test connectivity (ping PC from AI-Pi)

---

## 📝 File Locations Reference

### PC (Windows)
```
C:\Users\spenc\JARVIS-Workspace\
├── api\
│   ├── server.py              (WebSocket server)
│   └── README.md
├── core\
│   ├── jarvis_brain.py        (Brain intelligence)
│   ├── personality_engine.py
│   ├── context_manager.py
│   ├── proactive_engine.py
│   └── jarvis_memory_system.py
├── temp_ai_pi_modules\
│   ├── client.py              (AI-Pi WebSocket client)
│   ├── hotword.py
│   ├── recorder.py
│   ├── playback.py
│   ├── vad.py
│   └── vad_optimized.py
├── launch-ubuntu-jarvis.ps1   (Server launcher)
├── launch-ai-pi.ps1
├── launch-both.ps1
└── configure-c3-network.ps1   (Network setup)
```

### AI-Pi (Current Phase G5)
```
/home/spencer/
├── jarvis_terminal/
│   ├── voice_session.py       (Standalone voice mode)
│   ├── action_engine.py
│   ├── memory_engine.py
│   ├── task_engine.py
│   ├── planning_engine.py
│   ├── vault_engine.py
│   ├── core/
│   │   └── config.py
│   └── logs/
│       └── g5_voice_sessions.log
├── jarvis_terminal_env/       (Python venv)
└── jarvis_memory/             (ChromaDB storage)
```

### AI-Pi (Phase C3 Target)
```
/home/spencer/
├── jarvis_terminal/
│   ├── client.py              (WebSocket client)
│   ├── hotword.py
│   ├── recorder.py
│   ├── playback.py
│   └── vad.py
└── .env                       (JARVIS_WS_HOST, JARVIS_WS_PORT)
```

---

## 🎯 Recommended Next Steps

1. **Test Current G5:** Verify standalone voice_session.py works with TTS
2. **Document G5 Performance:** Measure actual latencies
3. **Decision Point:** Keep G5 standalone or migrate to C3 distributed?
4. **If Migrating:**
   - Backup AI-Pi current state
   - Set up PC Brain environment
   - Configure network
   - Test distributed system
   - Compare performance
5. **Hybrid Approach:** Support both modes with configuration flag

---

**Status:** Architecture documented. Ready for implementation decisions.

**Last Updated:** November 18, 2025  
**Next Review:** After G5 performance testing
