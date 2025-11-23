# JARVIS V1 STABILISATION STATUS
**Date:** 2025-11-19  
**Mission:** Persistent wake-word voice assistant with simple brain controls

---

## ✅ STEP 1: PERSISTENT BACKEND SERVICE (COMPLETE)

**Status:** `jarvis-backend.service` operational on Ai-Pi

**Implementation:**
- Service file: `/etc/systemd/system/jarvis-backend.service`
- ExecStart: `/home/spencer/jarvis_terminal_env/bin/python /home/spencer/jarvis_terminal/persistent_client.py`
- WorkingDirectory: `/home/spencer/jarvis_terminal`
- Enabled: `systemctl enable jarvis-backend.service`
- Auto-restart: `Restart=always`

**Behavior:**
- ✅ Starts automatically on Ai-Pi boot
- ✅ Attempts brain connection on startup (192.168.1.26:8765)
- ✅ Auto-reconnects every 30s if brain disconnected
- ✅ Processes queued requests when brain reconnects
- ✅ REST API accessible at `http://ai-pi.local:8766`
- ✅ `/api/state` and `/api/events` working
- ✅ CHECK_BRAIN button shows accurate status
- ✅ TEST TIME / PTT voice pipeline functional

**Verification:**
```bash
# On Ai-Pi after reboot:
systemctl status jarvis-backend.service  # Should show active (running)
curl http://localhost:8766/api/state     # Should return JSON with brain_connected status
```

---

## 🔨 STEP 2: BRAIN CONTROL GUI (IN PROGRESS)

**Goal:** Simple PC-side GUI to start/stop brain server

**Requirements:**
- [ ] Status indicator: Brain ONLINE / OFFLINE
- [ ] "Start Brain" button → launches WSL brain server with cuDNN
- [ ] "Stop Brain" button → cleanly stops brain process
- [ ] Optional: "Pause for Gaming" button (future)

**Current workaround:**
- Manual start: Run `start-brain-server.bat` on PC
- Manual stop: Close PowerShell window running brain

---

## 🔨 STEP 3: PERSISTENT WAKE WORD (IN PROGRESS)

**Goal:** Say "Jarvis" → full voice roundtrip (hands-free operation)

### 3A: Wake Word Integration
**Status:** Code exists but not enabled

**Existing code:**
- `voice_loop()` method in `persistent_client.py` (lines 449-521)
- Uses `HotwordDetector` from `hotword.py` (Porcupine)
- Porcupine access key configured
- Currently triggered by `start` action (not auto-started)

**Requirements:**
- [ ] Auto-start Porcupine listener when backend starts
- [ ] Use same audio device as PTT/TEST TIME
- [ ] Call `ptt_voice_interaction()` on wake detection
- [ ] Single voice pipeline (no duplicates)

### 3B: Noise Robustness
**Status:** Not implemented

**Requirements:**
- [ ] `is_speaking` flag during TTS playback → ignore wake detections
- [ ] 3-second cooldown after each wake event
- [ ] Moderate Porcupine sensitivity (0.5 default)
- [ ] Prevent self-triggering on Jarvis's own voice

---

## CURRENT SYSTEM STATE

**Ai-Pi Services:**
- `jarvis-backend.service` → **RUNNING** (auto-starts on boot)
- `jarvis-gui.service` → **RUNNING** (auto-starts on boot, serves GUI at :5000)

**PC Brain:**
- Status: **MANUAL START REQUIRED**
- Start method: `start-brain-server.bat` or PowerShell window
- Network: Accessible at `192.168.1.26:8765` from Ai-Pi

**Voice Pipeline:**
- PTT mode: **WORKING** (TEST TIME button in GUI)
- Wake word mode: **NOT ENABLED** (code exists, not auto-started)

---

## SUCCESS CRITERIA (V1 COMPLETE)

- [x] Ai-Pi boots → backend running automatically
- [ ] Sir starts Brain Control GUI → clicks "Start Brain"
- [x] GUI HUD shows Ai-Pi + Brain status truthfully
- [x] TEST TIME button works (manual PTT)
- [ ] Say "Jarvis" → voice roundtrip works hands-free
- [ ] No false triggers from background noise
- [ ] No self-triggering during Jarvis TTS playback

**When all checkboxes ticked:** JARVIS V1 READY 🎉

---

## FILES MODIFIED

**Ai-Pi:**
- `/etc/systemd/system/jarvis-backend.service` (created)
- `/etc/systemd/system/jarvis-gui.service` (created)
- `~/jarvis_terminal/persistent_client.py` (added reconnection loop)
- `~/jarvis_terminal/.env` (JARVIS_WS_HOST, JARVIS_WS_PORT)

**PC:**
- `JARVIS-Workspace/start-brain-server.bat` (created)
- `JARVIS-Workspace/launch-ubuntu-jarvis.ps1` (existing, for manual start)

---

## NEXT ACTIONS

1. **STEP 2:** Create simple Brain Control GUI (Python/tkinter or Electron)
2. **STEP 3A:** Enable `voice_loop()` in persistent_client startup
3. **STEP 3B:** Add noise robustness (is_speaking, cooldown)
4. **Final test:** Complete reboot → GUI → "Jarvis" → voice works
