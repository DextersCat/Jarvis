# Phase C3: The Great Link - Integration Report
**Date:** November 16, 2025  
**Phase:** JARVIS Awakening Sequence - Part 3  
**Status:** 🚧 IN PROGRESS

---

## 🎯 Objective

Complete voice integration between AI-Pi Voice Terminal and JARVIS Brain on PC.

**Flow:** Wake word → Voice capture → Stream to PC → Whisper → Brain → TTS → Play on AI-Pi

---

## ✅ PC Side - WebSocket Server (COMPLETED)

### 1. Server Implementation

**Location:** `~/JARVIS/api/websocket_server/server.py`

**Features Implemented:**
- ✅ Asyncio-based WebSocket server (websockets library)
- ✅ Listening on configurable host/port (default: 0.0.0.0:8765)
- ✅ JSON message protocol with UTF-8 text frames
- ✅ Audio buffering for utterances
- ✅ Whisper API integration for transcription
- ✅ JARVIS brain processing integration
- ✅ TTS audio generation and streaming
- ✅ Connection management and logging
- ✅ Error handling

**Server Capabilities:**
- Receives audio streams from AI-Pi
- Processes with GPU-accelerated Whisper
- Uses JARVIS personality framework
- Generates TTS responses
- Streams audio back to AI-Pi
- Logs all interactions

### 2. Launcher Script

**Location:** `~/JARVIS/api/websocket_server/run_server.py`

**Features:**
- ✅ Virtual environment detection
- ✅ Configuration via environment variables
- ✅ Graceful startup/shutdown
- ✅ Error handling

**Usage:**
```bash
cd ~/JARVIS/api/websocket_server
./run_server.py
```

---

## 📡 WebSocket Protocol Specification

### Message Format

All messages are JSON over WebSocket text frames (UTF-8):

```json
{
  "type": "message_type",
  "data": "optional_data",
  "message": "optional_message"
}
```

### Message Types

#### From AI-Pi → PC

**1. audio_start**
```json
{
  "type": "audio_start"
}
```
Marks the beginning of a new audio utterance.

**2. audio_chunk**
```json
{
  "type": "audio_chunk",
  "data": "base64_encoded_pcm_audio"
}
```
Audio data chunk (16-bit PCM, mono, 16kHz, base64-encoded).

**3. audio_end**
```json
{
  "type": "audio_end"
}
```
Marks the end of the audio utterance. Triggers processing.

**4. ping**
```json
{
  "type": "ping"
}
```
Health check request.

#### From PC → AI-Pi

**1. ack**
```json
{
  "type": "ack",
  "message": "audio_start acknowledged"
}
```
Acknowledgment of received messages.

**2. tts_chunk**
```json
{
  "type": "tts_chunk",
  "data": "base64_encoded_audio"
}
```
TTS audio data chunk (base64-encoded).

**3. tts_end**
```json
{
  "type": "tts_end"
}
```
Marks the end of TTS audio stream.

**4. pong**
```json
{
  "type": "pong"
}
```
Health check response.

**5. error**
```json
{
  "type": "error",
  "message": "error description"
}
```
Error notification.

---

## 🎵 Audio Format Specification

### Standard Format
- **Sample Rate:** 16,000 Hz (16 kHz)
- **Channels:** 1 (Mono)
- **Sample Width:** 16-bit (2 bytes per sample)
- **Encoding:** PCM (Pulse Code Modulation)
- **Byte Order:** Little-endian
- **Transport:** Base64-encoded in JSON

### Calculations
- **Bytes per second:** 16000 Hz × 1 channel × 2 bytes = 32,000 bytes/sec
- **1 second of audio:** ~32 KB
- **Chunk size:** 4096 bytes ≈ 128ms of audio

---

## 🔧 Configuration

### Environment Variables

**PC Brain (Ubuntu WSL2):**
```bash
# In ~/JARVIS/config/.env
OPENAI_API_KEY=your_key_here
JARVIS_WS_HOST=0.0.0.0        # Listen on all interfaces
JARVIS_WS_PORT=8765            # WebSocket port
```

**AI-Pi Terminal:**
```bash
# In ~/.env or ~/jarvis_terminal/config/.env
PORCUPINE_ACCESS_KEY=your_key_here
JARVIS_BRAIN_HOST=192.168.x.x  # PC IP address on LAN
JARVIS_BRAIN_PORT=8765         # WebSocket port
```

### Network Setup

**Finding PC IP Address:**
```bash
# On Ubuntu WSL2
ip addr show eth0 | grep "inet "
# Or
hostname -I
```

**Firewall (if needed):**
```bash
# Allow WebSocket port on Windows
# Windows Firewall → New Inbound Rule → Port 8765 → Allow
```

---

## 🥧 AI-Pi Side - Implementation Status

### Components Implementation - ✅ COMPLETE

#### 1. Hotword Detection (`audio/hotword/hotword.py`)

**Status:** ✅ IMPLEMENTED

**Key Implementation Points:**
```python
def wait_for_wakeword(self):
    """
    Wait for "jarvis" wake word using Porcupine
    Blocks until wake word detected
    """
    # Initialize Porcupine with keyword "jarvis"
    # Listen to microphone continuously
    # Return when keyword detected
```

**Dependencies:**
- pvporcupine (already installed)
- sounddevice (already installed)
- PORCUPINE_ACCESS_KEY from .env

#### 2. Voice Activity Detection (`audio/vad/vad.py`)

**Status:** ✅ IMPLEMENTED

**Key Implementation Points:**
```python
def should_continue_speaking(self, frame):
    """
    Determine if user is still speaking
    
    Logic:
    - Calculate RMS energy of frame
    - If energy > threshold: speech detected
    - Track consecutive silence frames
    - Stop if silence > 800-1200ms (12-18 frames @ 16kHz)
    - Stop if total duration > 8-10 seconds
    
    Returns: bool
    """
```

**Configuration:**
- Energy threshold: 0.02 (adjustable)
- Silence timeout: 1000ms
- Max duration: 10 seconds

#### 3. Audio Recorder (`audio/recorder/recorder.py`)

**Status:** ✅ IMPLEMENTED

**Key Implementation Points:**
```python
def record_until_silence(self, vad):
    """
    Record audio until VAD detects end of speech
    
    Flow:
    1. Start sounddevice input stream (16kHz mono)
    2. Collect frames
    3. Check each frame with VAD
    4. Stop when VAD says stop
    5. Return complete audio as bytes
    """
```

#### 4. WebSocket Client (`networking/websocket_client/client.py`)

**Status:** ✅ IMPLEMENTED

**Key Implementation Points:**
```python
async def stream_audio_to_brain(self, audio_data):
    """
    Stream audio to PC brain
    
    Steps:
    1. Connect to ws://PC_IP:8765
    2. Send audio_start
    3. Split audio into chunks
    4. Send audio_chunk for each
    5. Send audio_end
    6. Wait for TTS response
    7. Yield TTS chunks as they arrive
    """
```

#### 5. Audio Playback (`audio/playback/playback.py`)

**Status:** ✅ IMPLEMENTED & TESTED

**Key Implementation Points:**
```python
def play_tts_stream(self, audio_chunks):
    """
    Play TTS audio as it arrives
    
    - Use sounddevice for playback
    - Handle streaming (don't wait for all data)
    - Proper format handling (MP3 vs PCM)
    """
```

---

## 🧪 Integration Tests

### C3-T1: PC-Only Test

**Objective:** Verify PC brain processing pipeline

**Steps:**
1. Start WebSocket server on PC
2. Create test client script
3. Send test audio (pre-recorded "Hello JARVIS")
4. Verify:
   - ✅ Audio received
   - ✅ Whisper transcription works
   - ✅ Brain processes correctly
   - ✅ TTS generated
   - ✅ Audio streamed back

**Status:** 📋 Ready to test

**Test Script Location:** `~/JARVIS/tests/test_c3_server.py` (to be created)

### C3-T2: Link Test (AI-Pi ↔ PC)

**Objective:** Verify AI-Pi to PC communication

**Steps:**
1. Start server on PC
2. From AI-Pi, run test client
3. Send programmatic audio
4. Verify:
   - ✅ Connection established
   - ✅ Audio transmitted
   - ✅ Response received
   - ✅ Audio playback works

**Status:** ⏳ Awaiting AI-Pi implementation

### C3-T3: Full Live Test

**Objective:** End-to-end voice interaction

**Test Procedure:**
1. Start PC WebSocket server
2. Start AI-Pi voice terminal
3. Say wake word: "JARVIS"
4. Speak: "Who are you and what is your purpose?"
5. Verify:
   - ✅ Wake word detected
   - ✅ Voice captured
   - ✅ Audio streamed to PC
   - ✅ JARVIS responds (British butler personality)
   - ✅ TTS audio plays on AI-Pi speakers
   - ✅ No prompt leakage
   - ✅ Response time acceptable

**Status:** ⏳ Awaiting full implementation

**Expected Response:**
> "Good day, sir. I am JARVIS, your personal AI assistant. My purpose is to 
> provide you with efficient, intelligent assistance across a wide range of 
> tasks. I'm here to make your life easier through thoughtful analysis, 
> proactive suggestions, and reliable execution. How may I be of service?"

---

## 📊 System Architecture

### Complete Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     AI-Pi Voice Terminal                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [1] Wake Word Detection                                   │
│      hotword.py → Porcupine → "JARVIS" detected            │
│            ↓                                                │
│                                                             │
│  [2] Audio Capture                                         │
│      recorder.py → sounddevice → USB mic                   │
│            ↓                                                │
│                                                             │
│  [3] Voice Activity Detection                              │
│      vad.py → Energy-based → Stop on silence               │
│            ↓                                                │
│                                                             │
│  [4] WebSocket Client                                      │
│      client.py → Encode PCM → Base64                       │
│            ↓                                                │
│      ╔════════════════════════════════╗                    │
│      ║  ws://PC_IP:8765               ║                    │
│      ║  JSON Protocol                 ║                    │
│      ║  • audio_start                 ║                    │
│      ║  • audio_chunk (streaming)     ║                    │
│      ║  • audio_end                   ║                    │
│      ╚════════════════════════════════╝                    │
│            ↓                                                │
└─────────────────────────────────────────────────────────────┘
                       ↓
                    NETWORK
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                  PC Brain (Ubuntu WSL2)                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [5] WebSocket Server                                      │
│      server.py → Receive JSON → Buffer audio               │
│            ↓                                                │
│                                                             │
│  [6] Audio Processing                                      │
│      Decode Base64 → Create WAV → 16kHz PCM                │
│            ↓                                                │
│                                                             │
│  [7] Whisper Transcription (GPU)                           │
│      OpenAI Whisper API → Text                             │
│            ↓                                                │
│                                                             │
│  [8] JARVIS Brain Processing                               │
│      jarvis_brain.py:                                      │
│      • PersonalityEngine                                   │
│      • ContextManager                                      │
│      • JARVISMemory (ChromaDB)                             │
│      • ProactiveSuggestionEngine                           │
│      • GPT-4 Processing                                    │
│            ↓                                                │
│                                                             │
│  [9] TTS Generation                                        │
│      OpenAI TTS API → Audio bytes                          │
│            ↓                                                │
│                                                             │
│  [10] Response Streaming                                   │
│       Encode Base64 → JSON chunks                          │
│       ╔════════════════════════════════╗                   │
│       ║  • tts_chunk (streaming)       ║                   │
│       ║  • tts_chunk                   ║                   │
│       ║  • tts_end                     ║                   │
│       ╚════════════════════════════════╝                   │
│            ↓                                                │
└─────────────────────────────────────────────────────────────┘
                       ↓
                    NETWORK
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                     AI-Pi Voice Terminal                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [11] Receive TTS Audio                                    │
│       client.py → Decode Base64 → Audio bytes              │
│            ↓                                                │
│                                                             │
│  [12] Audio Playback                                       │
│       playback.py → sounddevice → Speakers                 │
│            ↓                                                │
│                                                             │
│       🔊 JARVIS speaks!                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 💻 Quick Start Guide

### PC Side Setup

```bash
# 1. Navigate to server directory
cd ~/JARVIS/api/websocket_server

# 2. Activate virtual environment
source ~/jarvis_env/bin/activate

# 3. Verify dependencies
pip list | grep -E "websockets|openai"

# 4. Set environment (if needed)
export JARVIS_WS_HOST=0.0.0.0
export JARVIS_WS_PORT=8765

# 5. Start server
./run_server.py

# Output:
# ============================================================
# JARVIS BRAIN WEBSOCKET SERVER
# ============================================================
# Server starting on ws://0.0.0.0:8765
# Audio format: 16000Hz, 1ch, 16-bit PCM
# Log file: ~/JARVIS/runtime/logs/phase_c3_server_*.log
# ============================================================
# Waiting for AI-Pi connections...
```

### AI-Pi Side Setup (When Implemented)

```bash
# 1. Navigate to terminal directory
cd ~/jarvis_terminal

# 2. Activate virtual environment
source ~/jarvis_terminal_env/bin/activate

# 3. Configure PC connection
export JARVIS_BRAIN_HOST=192.168.1.xxx  # Your PC IP
export JARVIS_BRAIN_PORT=8765

# 4. Run voice terminal
python3 main.py

# Terminal will:
# - Initialize components
# - Wait for wake word
# - Stream audio to PC
# - Play responses
```

---

## 📋 Implementation Checklist

### PC Side ✅
- [x] WebSocket server implementation
- [x] JSON protocol handling
- [x] Audio buffering
- [x] Whisper integration
- [x] JARVIS brain integration
- [x] TTS generation
- [x] Audio streaming
- [x] Logging system
- [x] Launcher script
- [x] Server tested and running

### AI-Pi Side ✅
- [x] Hotword detection implementation
- [x] VAD implementation
- [x] Audio recorder implementation
- [x] WebSocket client implementation
- [x] Audio playback implementation
- [x] Main integration script
- [x] Error handling
- [x] Logging system
- [x] Playback tested successfully

### Testing ⚠️
- [x] PC server initialization test
- [x] AI-Pi playback test
- [ ] C3-T1: PC-only pipeline test (pending)
- [ ] C3-T2: AI-Pi ↔ PC link test (blocked on networking)
- [ ] C3-T3: Full live voice test (blocked on networking)
- [ ] Latency measurements
- [ ] Error recovery testing
- [ ] Extended conversation testing

### Networking Configuration ⚠️
- [ ] WSL2 port forwarding configured
- [ ] Windows firewall rule created
- [ ] AI-Pi to PC connectivity verified
- [ ] Porcupine API key set on AI-Pi

---

## 🚧 Current Status

**PC Brain WebSocket Server:** ✅ COMPLETE
- Fully implemented and ready to test
- Integrated with JARVIS brain
- Whisper and TTS ready
- Logging configured

**AI-Pi Voice Terminal:** 📋 READY FOR IMPLEMENTATION
- Skeleton code in place
- Dependencies installed
- Hardware tested
- Ready for logic implementation

**Next Steps:**
1. Implement AI-Pi components (hotword, VAD, recorder, client, playback)
2. Create main integration script for AI-Pi
3. Run C3-T1 (PC-only test)
4. Run C3-T2 (link test)
5. Run C3-T3 (full live test)
6. Document results and optimize

---

**Report Status:** 🚧 IN PROGRESS  
**Last Updated:** November 16, 2025  
**Phase:** C3 - The Great Link  
**PC Side:** ✅ Complete  
**AI-Pi Side:** ✅ Complete (all 5 modules implemented)
**Testing:** 🔄 In Progress

---

## 📊 Test Results

### Component Tests

#### ✅ AI-Pi Playback Test (November 16, 2025 14:14 UTC)

**Test:** `python3 audio/playback/playback.py`

**Results:**
- Test 1 (440Hz tone, 1s): ✅ PASS
- Test 2 (880Hz tone, 0.5s): ✅ PASS
- Test 3 (PCM beep pattern): ✅ PASS

**Audio Devices Detected:**
- [0] vc4-hdmi-0: MAI PCM i2s-hifi-0 (hw:0,0) - 2ch
- [2] sysdefault - 128ch
- [3] hdmi - 2ch
- [4] pipewire - 64ch
- [5] default - 64ch

**Status:** ✅ Playback module fully functional

#### ✅ PC WebSocket Server Test (November 16, 2025 14:16 UTC)

**Test:** Server startup and initialization

**Results:**
- Server initialization: ✅ PASS (9.1 seconds)
- Brain loading: ✅ PASS
- ChromaDB initialization: ✅ PASS
- SentenceTransformer loading: ✅ PASS (all-MiniLM-L6-v2)
- WebSocket listening: ✅ PASS (ws://0.0.0.0:8765)

**Initialization Time:**
- Total: 9.1 seconds
- SentenceTransformer load: 5.0 seconds
- Other components: 4.1 seconds

**Status:** ✅ Server ready and listening

#### ⚠️ AI-Pi to PC Connection Test (November 16, 2025 14:16 UTC)

**Test:** WebSocket client connection from AI-Pi to PC

**Configuration:**
- PC IP: 172.25.232.253 (WSL2)
- Port: 8765
- Protocol: WebSocket (ws://)

**Results:**
- Connection attempt: ❌ TIMEOUT (10 seconds)
- Issue: Network connectivity between AI-Pi and WSL2

**Known Issue:**
WSL2 networking requires additional configuration to allow external devices to connect. The WSL2 IP (172.25.232.253) is on a virtual network that may not be accessible from AI-Pi on the LAN.

**Workarounds to Test:**
1. **Use Windows Host IP:** Forward port from Windows to WSL2
2. **Test Locally First:** Run client test from within WSL2
3. **Network Bridge:** Configure WSL2 in bridged mode

**Next Steps:**
- Configure port forwarding: Windows → WSL2 port 8765
- Or test with simpler setup (PC server running on Windows directly)
- Or use direct IP routing between AI-Pi and WSL2

**Status:** 🔄 Networking configuration needed

### Implementation Summary

#### Completed Components (8/8)

**PC Side:**
1. ✅ WebSocket Server (server.py) - 13KB, full protocol implementation
2. ✅ Server Launcher (run_server.py) - Environment validation & startup

**AI-Pi Side:**
1. ✅ Audio Playback (playback.py) - 6.3KB, sounddevice integration
2. ✅ WebSocket Client (client.py) - 11KB, backoff reconnection
3. ✅ Hotword Detection (hotword.py) - 6KB, Porcupine integration
4. ✅ Voice Activity Detection (vad.py) - 7.5KB, energy-based VAD
5. ✅ Audio Recorder (recorder.py) - 8.6KB, full integration
6. ✅ Integration Test Script (recorder.py main) - Full pipeline test

**Total Code:** ~52.4KB of production Python code

#### Test Status

- ✅ Playback: Fully tested and working
- ✅ Server: Initialized and listening
- ⚠️ Network: WSL2 connectivity issue (workaround needed)
- ⏳ Hotword: Ready to test (requires Porcupine key)
- ⏳ VAD: Ready to test (integrated in recorder)
- ⏳ Full Pipeline: Pending network resolution

---

## 🚀 Next Steps for User

### Immediate Actions

1. **Configure WSL2 Networking**

   **Option A: Port Forwarding (Recommended)**
   ```powershell
   # On Windows (run as Administrator)
   netsh interface portproxy add v4tov4 listenport=8765 listenaddress=0.0.0.0 connectport=8765 connectaddress=172.25.232.253
   
   # Allow through Windows Firewall
   New-NetFirewallRule -DisplayName "JARVIS WebSocket" -Direction Inbound -LocalPort 8765 -Protocol TCP -Action Allow
   ```
   
   Then test from AI-Pi using Windows PC IP (not WSL IP).

   **Option B: Test Locally First**
   ```bash
   # On Ubuntu WSL2
   cd ~/jarvis_terminal
   source ~/jarvis_terminal_env/bin/activate
   export JARVIS_WS_HOST=localhost
   export JARVIS_WS_PORT=8765
   python3 networking/websocket_client/client.py
   ```

2. **Set Porcupine API Key on AI-Pi**

   ```bash
   # On AI-Pi
   export PORCUPINE_ACCESS_KEY=your_key_here
   # Or add to ~/.bashrc or ~/jarvis_terminal/config/.env
   ```

3. **Test Individual Components**

   ```bash
   # On AI-Pi
   cd ~/jarvis_terminal
   source ~/jarvis_terminal_env/bin/activate
   
   # Test hotword detection (requires Porcupine key)
   python3 audio/hotword/hotword.py
   
   # Test VAD
   python3 audio/vad/vad.py
   ```

4. **Full Integration Test**

   Once networking is resolved:
   ```bash
   # On PC (WSL2)
   cd ~/JARVIS/api/websocket_server
   source ~/jarvis_env/bin/activate
   ./run_server.py
   
   # On AI-Pi (separate terminal)
   export JARVIS_WS_HOST=<your_pc_ip>
   export JARVIS_WS_PORT=8765
   export PORCUPINE_ACCESS_KEY=<your_key>
   cd ~/jarvis_terminal
   source ~/jarvis_terminal_env/bin/activate
   python3 audio/recorder/recorder.py
   
   # Say "JARVIS" then speak your question
   ```

### Configuration Files Needed

Create `~/jarvis_terminal/config/.env` on AI-Pi:
```bash
JARVIS_WS_HOST=<your_windows_pc_ip>
JARVIS_WS_PORT=8765
PORCUPINE_ACCESS_KEY=<your_porcupine_key>
```

Update `~/JARVIS/config/.env` on Ubuntu (if needed):
```bash
JARVIS_WS_HOST=0.0.0.0
JARVIS_WS_PORT=8765
OPENAI_API_KEY=<your_key>
```

---

**Report Status:** ✅ IMPLEMENTATION COMPLETE - Networking Configuration Needed  
**Last Updated:** November 16, 2025 14:20 UTC  
**Phase:** C3 - The Great Link  
**PC Side:** ✅ Complete & Running  
**AI-Pi Side:** ✅ Complete (all 5 modules)  
**Testing:** ⚠️ Blocked on WSL2 networking (workaround provided)
