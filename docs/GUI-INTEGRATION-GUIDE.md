# GUI Integration Guide - Jarvis HUD

**Last Updated:** 2025-11-19  
**Status:** ✅ OPERATIONAL

## Quick Start

### Terminal 1 - Python Backend
```bash
cd ~/jarvis_terminal
~/jarvis_terminal_env/bin/python persistent_client.py
# Keep running - serves API on port 8766
```

### Terminal 2 - GUI Server
```bash
cd ~/jarvis_gui
npm start
# Keep running - serves HUD on port 5000
```

### Browser
```
http://localhost:5000
```

## Architecture

```
Browser (Chromium/Firefox)
    ↓ GET /api/state, /api/events (every 1 second)
    ↓ POST /api/action (button clicks)
Express Server (port 5000)
    ↓ Proxy forwards to localhost:8766
Python REST API (aiohttp, port 8766)
    ↓ Managed by
persistent_client.py (headless daemon)
```

## Key Files

### Backend (Python)
- `~/jarvis_terminal/persistent_client.py` - Main daemon
- `~/jarvis_terminal/api/api_server.py` - REST API server (aiohttp)

### Frontend (Node/React)
- `~/jarvis_gui/server/routes.ts` - **Express proxy middleware**
- `~/jarvis_gui/client/src/pages/jarvis-hud.tsx` - **Main HUD component**
- `~/jarvis_gui/package.json` - Build scripts

## API Endpoints

### GET /api/state
Returns current system state:
```json
{
  "core_state": "listening",
  "loop_running": true,
  "brain_connected": false,
  "wake_mode": "PTT",
  "last_audio_time": null,
  "model_label": "Offline",
  "last_brain_action": "Brain: localhost:8765"
}
```

### GET /api/events
Returns recent events:
```json
{
  "events": [
    {"timestamp": "10:28:42", "message": "Time test: 10:28:42"},
    {"timestamp": "10:28:39", "message": "Brain check: disconnected"}
  ]
}
```

### POST /api/action
Triggers backend actions:
```json
{"action": "start"}       // Start Jarvis loop
{"action": "stop"}        // Stop Jarvis loop
{"action": "test_time"}   // Test local query handler
{"action": "check_brain"} // Ping brain connection
```

## HUD Display

### Left Panel (AI-Pi)
- Loop status: RUNNING / STOPPED
- Wake mode: PTT / Always / Voice
- Local time: Updates every second
- Last audio: Timestamp of last capture

### Right Panel (Brain)
- Brain: ONLINE / OFFLINE
- Model: OpenAI / Offline
- Last Action: Most recent brain command

### Bottom Panel
- Event Log: Last 50 timestamped events
- Control Buttons: 4 action buttons

## Troubleshooting

### CORS Errors
**Should never happen** - proxy eliminates CORS.  
If you see CORS errors:
1. Verify proxy in `~/jarvis_gui/server/routes.ts` has `app.all('/api/*', ...)`
2. Verify HUD uses relative paths: `fetch('/api/state')` not `fetch('http://...')`
3. Rebuild GUI: `cd ~/jarvis_gui && npm run build`

### 502 Bad Gateway
Python API not responding:
```bash
# Check if running
pgrep -f persistent_client.py

# Restart if needed
pkill -9 -f persistent_client.py
cd ~/jarvis_terminal
~/jarvis_terminal_env/bin/python persistent_client.py
```

### GUI Not Loading
```bash
# Check if server running
pgrep -f "node dist/index.js"

# Restart
cd ~/jarvis_gui
pkill -f "node dist/index.js"
npm start
```

### Buttons Don't Work
Check browser console (F12 → Console):
- Should see `Starting Jarvis...` when button clicked
- Should see POST to `/api/action` in Network tab
- No red errors

Check Terminal 1 (Python):
- Should see `POST /api/action HTTP/1.1 200` logs

## Build Process

### Full Rebuild
```bash
cd ~/jarvis_gui
npm run build
# Output: dist/public/ (static assets) + dist/index.js (server)
```

### Development vs Production
- Development: `npm run dev` (Vite hot reload)
- Production: `npm run build` then `npm start` (static serve)

Currently using **production mode** for stability.

## Implementation Details

### Proxy Configuration (routes.ts)
```typescript
app.all('/api/*', async (req, res) => {
  const apiPath = req.url;
  const targetUrl = `http://localhost:8766${apiPath}`;
  
  const response = await fetch(targetUrl, {
    method: req.method,
    headers: {'Content-Type': 'application/json'},
    body: req.method !== 'GET' ? JSON.stringify(req.body) : undefined,
  });
  
  const data = await response.json();
  res.status(response.status).json(data);
});
```

### HUD Polling (jarvis-hud.tsx)
```typescript
useEffect(() => {
  const pollAPI = async () => {
    const stateRes = await fetch('/api/state');
    const eventsRes = await fetch('/api/events');
    // Update React state
  };
  
  pollAPI(); // Immediate
  const interval = setInterval(pollAPI, 1000); // Every second
  return () => clearInterval(interval);
}, []);
```

### Button Handlers (jarvis-hud.tsx)
```typescript
const handleStartJarvis = async () => {
  await fetch('/api/action', {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({action: "start"})
  });
};
```

## Next Steps

1. **Complete systemd services** - Auto-start backend and GUI on boot
2. **Start PC Brain server** - Whisper + GPT + TTS on WSL (192.168.1.26:8765)
3. **Integrate voice capture** - PTT button on Ai-Pi triggers recording
4. **Complete voice roundtrip** - Voice → Brain → Response → Playback
5. **Test offline queueing** - Voice queries queue when brain offline, flush when online

## Critical Notes

- **Jarvis is VOICE ONLY** - No text queries, no text interface
- **Brain = Whisper + GPT + TTS** - All voice processing happens on PC
- **Queue = Voice queries** - Not button actions (those are local)
- **RequestQueue exists** - File-based persistence already implemented
- **Services after behavior** - Prove voice roundtrip works before daemonizing

## Notes

- **No CORS middleware needed in Python** - proxy handles it
- **Use relative paths** in all frontend fetch calls
- **Python runs headless** - no stdin/stdout interaction
- **GUI is visualization only** - Python backend is source of truth
- **Port 5000 serves everything** - browser sees single origin

---
**Maintained by:** Nexus  
**Approved by:** Astra  
**Reference:** STATE_OF_JARVIS.md
