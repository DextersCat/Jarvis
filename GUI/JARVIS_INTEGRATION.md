# Jarvis AI Console — Python Backend Integration Guide

This document explains how to integrate your Python backend (Ai-Pi) with the Jarvis AI Console HUD.

## Overview

The Jarvis HUD provides a WebSocket server and REST API endpoints that your Python backend can use to update the interface in real-time. The interface will automatically reflect any changes sent from your backend.

## Connection Methods

### 1. WebSocket (Real-time Updates)

The WebSocket server is available at: `ws://localhost:5000/jarvis-ws`

**Message Format:**
All WebSocket messages use JSON format. The frontend automatically processes these message types:

```json
{
  "type": "updateCoreState",
  "state": "listening" | "processing" | "speaking" | "online" | "offline" | "stopped"
}

{
  "type": "updateLoopState",
  "isRunning": true | false
}

{
  "type": "updateBrainStatus",
  "isOnline": true | false,
  "modelLabel": "Local LLM" | "OpenAI" | "...",
  "lastAction": "TIME_INTENT handled"
}

{
  "type": "updateAiPiStatus",
  "wakeMode": "PTT" | "Wake word" | "Both",
  "lastAudioTime": "14:23:45"
}

{
  "type": "addEventLog",
  "message": "Your event message here"
}
```

**Python WebSocket Example:**

```python
import websocket
import json

# Connect to Jarvis WebSocket
ws = websocket.create_connection("ws://localhost:5000/jarvis-ws")

# Update core state to listening
ws.send(json.dumps({
    "type": "updateCoreState",
    "state": "listening"
}))

# Add an event to the log
ws.send(json.dumps({
    "type": "addEventLog",
    "message": "Wake word detected"
}))

ws.close()
```

### 2. HTTP REST API (Simple Updates)

If WebSocket is too complex, you can use simple HTTP POST requests:

**Base URL:** `http://localhost:5000/api/jarvis`

**Endpoints:**

1. **Update Core State**
   ```bash
   POST /api/jarvis/core-state
   Content-Type: application/json
   
   {
     "state": "listening"
   }
   ```

2. **Update Loop State**
   ```bash
   POST /api/jarvis/loop-state
   Content-Type: application/json
   
   {
     "isRunning": true
   }
   ```

3. **Update Brain Status**
   ```bash
   POST /api/jarvis/brain-status
   Content-Type: application/json
   
   {
     "isOnline": true,
     "modelLabel": "Local LLM",
     "lastAction": "TIME_INTENT handled"
   }
   ```

4. **Update AI-Pi Status**
   ```bash
   POST /api/jarvis/ai-pi-status
   Content-Type: application/json
   
   {
     "wakeMode": "PTT",
     "lastAudioTime": "14:23:45"
   }
   ```

5. **Add Event Log**
   ```bash
   POST /api/jarvis/event
   Content-Type: application/json
   
   {
     "message": "User query processed"
   }
   ```

**Python HTTP Example:**

```python
import requests
import json

BASE_URL = "http://localhost:5000/api/jarvis"

def update_core_state(state):
    """Update the neural network visual state"""
    requests.post(f"{BASE_URL}/core-state", json={"state": state})

def update_brain_status(is_online, model="Local LLM", last_action=""):
    """Update brain panel status"""
    requests.post(f"{BASE_URL}/brain-status", json={
        "isOnline": is_online,
        "modelLabel": model,
        "lastAction": last_action
    })

def add_event(message):
    """Add an event to the log"""
    requests.post(f"{BASE_URL}/event", json={"message": message})

# Usage example
update_core_state("listening")
add_event("Wake word detected")
update_core_state("processing")
add_event("Processing user intent")
update_brain_status(True, "Local LLM", "TIME_INTENT handled")
update_core_state("speaking")
add_event("Speaking response")
```

## Integration with Your InterfaceAdapter

Here's how to integrate with your existing Ai-Pi `InterfaceAdapter`:

```python
import requests

class JarvisHUDAdapter:
    """Adapter to send updates to the Jarvis HUD"""
    
    def __init__(self, base_url="http://localhost:5000/api/jarvis"):
        self.base_url = base_url
    
    def update_core_state(self, state):
        """
        Update the central neural network visualization state
        States: 'offline', 'online', 'listening', 'processing', 'speaking', 'stopped'
        """
        try:
            requests.post(f"{self.base_url}/core-state", 
                         json={"state": state}, 
                         timeout=0.5)
        except Exception as e:
            print(f"Failed to update HUD core state: {e}")
    
    def update_loop_state(self, is_running):
        """Update whether the AI-Pi loop is running"""
        try:
            requests.post(f"{self.base_url}/loop-state", 
                         json={"isRunning": is_running}, 
                         timeout=0.5)
        except Exception as e:
            print(f"Failed to update HUD loop state: {e}")
    
    def update_brain_status(self, is_online, model_label=None, last_action=None):
        """Update brain connection and activity status"""
        try:
            payload = {"isOnline": is_online}
            if model_label:
                payload["modelLabel"] = model_label
            if last_action:
                payload["lastAction"] = last_action
            requests.post(f"{self.base_url}/brain-status", 
                         json=payload, 
                         timeout=0.5)
        except Exception as e:
            print(f"Failed to update HUD brain status: {e}")
    
    def update_ai_pi_status(self, wake_mode=None, last_audio_time=None):
        """Update AI-Pi specific status information"""
        try:
            payload = {}
            if wake_mode:
                payload["wakeMode"] = wake_mode
            if last_audio_time:
                payload["lastAudioTime"] = last_audio_time
            requests.post(f"{self.base_url}/ai-pi-status", 
                         json=payload, 
                         timeout=0.5)
        except Exception as e:
            print(f"Failed to update HUD AI-Pi status: {e}")
    
    def add_event(self, message):
        """Add an event to the HUD event log"""
        try:
            requests.post(f"{self.base_url}/event", 
                         json={"message": message}, 
                         timeout=0.5)
        except Exception as e:
            print(f"Failed to add HUD event: {e}")

# Usage in your main loop:
hud = JarvisHUDAdapter()

# On startup
hud.update_loop_state(True)
hud.update_brain_status(True, "Local LLM")
hud.add_event("Jarvis system started")

# When wake word detected
hud.update_core_state("listening")
hud.add_event("Wake word detected")

# When processing
hud.update_core_state("processing")
hud.add_event("Processing user intent")

# When brain responds
hud.update_brain_status(True, "Local LLM", "TIME_INTENT handled")
hud.update_core_state("speaking")
hud.add_event("Playing response")

# Back to idle
hud.update_core_state("online")
```

## Core State Values

The neural network visualization responds to these states:

- `offline` - Dim, minimal animation (system not ready)
- `stopped` - Same as offline (system explicitly stopped)
- `online` - Gentle pulsing, ready state
- `listening` - Active state, waiting for input
- `processing` - Rapid pulsing animation, brain is thinking
- `speaking` - Active state, outputting response

## Tips for Smooth Integration

1. **Use timeouts**: Network calls should have short timeouts (0.5s) to avoid blocking your main loop
2. **Fire and forget**: Don't wait for responses unless you need to verify the update
3. **Batch updates**: If updating multiple values at once, make separate calls for each endpoint
4. **Error handling**: Wrap all HUD updates in try/except to prevent crashes if the HUD is offline
5. **Performance**: HTTP REST calls are simplest but WebSocket is more efficient for frequent updates

## Testing the Integration

You can test the HUD updates using curl:

```bash
# Update core state to listening
curl -X POST http://localhost:5000/api/jarvis/core-state \
  -H "Content-Type: application/json" \
  -d '{"state": "listening"}'

# Add an event
curl -X POST http://localhost:5000/api/jarvis/event \
  -H "Content-Type: application/json" \
  -d '{"message": "Test event from curl"}'
```

## Running on Raspberry Pi 5

The HUD is optimized for Raspberry Pi 5 performance:

1. Lightweight Canvas-based neural network (no heavy 3D rendering)
2. Minimal animations and transitions
3. Efficient WebSocket communication
4. Single-page application with no routing overhead

Simply deploy this application to your Pi and access it via browser at `http://raspberrypi.local:5000`

## Questions?

The frontend will automatically reconnect if the WebSocket connection drops, and all state updates are real-time. You can open the browser console to see connection status and debug any integration issues.
