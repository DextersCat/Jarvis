# Codex Integration Guide - JARVIS HUD

## Overview

The JARVIS HUD now includes two new interactive components for conversational AI integration at 2560x1440 resolution:

1. **Codex Text Entry Field** (Bottom Right) - Large textarea for user commands/queries
2. **Reply Options Panel** (Left Column, Bottom) - Clickable conversational response choices

Both components are designed to integrate with your Python backend (Ai-Pi) for natural language interactions.

---

## Layout Changes for 2560x1440

### Side Panel Structure (Mirrored Design)

**Left Column (420px):**
- **DIAGNOSTICS** (top) - System health metrics
- **REPLY OPTIONS** (bottom) - Conversational interaction buttons

**Right Column (420px):**
- **NEURAL UPLINK** (top) - Connection status and model info
- **OFFLINE QUEUE** (bottom) - Pending offline requests

**Bottom Section (288px height, split 50/50):**
- **Event Log** (left) - Terminal-style scrolling log
- **Codex Interface** (right) - Text entry + control buttons

---

## 1. Codex Text Entry Field

### Location
Bottom right section of the HUD (right half of bottom panel)

### UI Components
- Large textarea with placeholder: "Enter command or query for Jarvis..."
- **TRANSMIT** button - Primary submit action
- **INIT** button - Initialize system
- **GAME** toggle - Gaming mode on/off
- **EXIT** button - Shutdown system

### Keyboard Shortcuts
- **Ctrl+Enter** or **Cmd+Enter** - Submit textarea content

### API Endpoint

**POST `/api/codex`**

Request body:
```json
{
  "input": "User's command or query text here"
}
```

### Frontend Implementation

Location: `client/src/pages/jarvis-hud.tsx`

```typescript
const handleCodexSubmit = async (e?: React.FormEvent) => {
  e?.preventDefault();
  if (!codexInput.trim()) return;
  
  try {
    const res = await fetch(`${API_URL}/codex`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input: codexInput })
    });
    
    if (res.ok) {
      setCodexInput(''); // Clear input after successful submit
    }
  } catch (e) {
    console.error('Codex submit error:', e);
  }
};
```

### Backend Integration Points

You should implement the `/api/codex` endpoint in your Python backend to:

1. Receive the user's text input
2. Process it through your AI/LLM model
3. Optionally update the HUD state via WebSocket:
   - Change visualization state (LISTENING → PROCESSING → SPEAKING)
   - Add response to event log
   - Populate reply options for follow-up interactions

Example Python backend handler:
```python
@app.post('/api/codex')
async def handle_codex_command(request):
    data = await request.json()
    user_input = data.get('input', '')
    
    # Update HUD to PROCESSING state
    await broadcast_websocket({
        'type': 'updateCoreState',
        'state': 'processing'
    })
    
    # Process with your AI model
    response = await process_with_ai(user_input)
    
    # Add to event log
    await broadcast_websocket({
        'type': 'addEventLog',
        'message': f'CODEX: {response[:100]}...'
    })
    
    # Optionally set reply options for follow-up
    await broadcast_websocket({
        'type': 'updateReplyOptions',
        'options': ['Tell me more', 'Explain differently', 'Move to next topic']
    })
    
    # Return to IDLE state
    await broadcast_websocket({
        'type': 'updateCoreState',
        'state': 'idle'
    })
    
    return {'status': 'ok', 'response': response}
```

---

## 2. Reply Options Panel

### Location
Left column, bottom section (below DIAGNOSTICS panel) - mirrors the QUEUE panel layout

### UI Components
- Header: "REPLY OPTIONS"
- Numbered clickable buttons (e.g., "#1", "#2", "#3")
- Shows "No active options" when empty
- Cyan-themed buttons with hover glow effects

### API Endpoint

**POST `/api/reply`**

Request body:
```json
{
  "reply": "Selected option text"
}
```

### Frontend Implementation

Location: `client/src/pages/jarvis-hud.tsx`

```typescript
const [replyOptions, setReplyOptions] = useState<string[]>([]);

const handleReplyOptionClick = async (option: string) => {
  try {
    await fetch(`${API_URL}/reply`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reply: option })
    });
  } catch (e) {
    console.error('Reply option error:', e);
  }
};
```

### Backend Integration Points

You should implement the `/api/reply` endpoint to handle conversational choices:

Example Python backend handler:
```python
@app.post('/api/reply')
async def handle_reply_option(request):
    data = await request.json()
    selected_reply = data.get('reply', '')
    
    # Update state to PROCESSING
    await broadcast_websocket({
        'type': 'updateCoreState',
        'state': 'processing'
    })
    
    # Process the selected reply
    response = await handle_conversation_choice(selected_reply)
    
    # Add to event log
    await broadcast_websocket({
        'type': 'addEventLog',
        'message': f'USER SELECTED: {selected_reply}'
    })
    
    # Clear old options, set new ones based on context
    new_options = generate_new_reply_options(response)
    await broadcast_websocket({
        'type': 'updateReplyOptions',
        'options': new_options
    })
    
    return {'status': 'ok'}
```

---

## 3. WebSocket Message Protocol

### New Message Type: Update Reply Options

**Frontend State Management:**
```typescript
const [replyOptions, setReplyOptions] = useState<string[]>([]);
```

**WebSocket Message from Backend:**
```json
{
  "type": "updateReplyOptions",
  "options": [
    "Tell me more about this topic",
    "Show me an example",
    "Move to next section",
    "I understand, continue"
  ]
}
```

**Frontend Handler (add to existing WebSocket message handler):**
```typescript
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'updateReplyOptions':
      setReplyOptions(message.options || []);
      break;
    // ... existing cases ...
  }
};
```

---

## 4. Integration Workflow Example

### Scenario: User asks "What's the weather like?"

1. **User types in Codex field**: "What's the weather like?"
2. **User presses Ctrl+Enter** or clicks TRANSMIT
3. **Frontend** → POST to `/api/codex` with `{"input": "What's the weather like?"}`
4. **Backend** receives request:
   - Sets state to PROCESSING via WebSocket
   - Queries weather API
   - Generates response: "It's 72°F and sunny in your location"
   - Broadcasts event log entry
   - Sets reply options: ["Show forecast", "Weather alerts?", "Set reminder"]
   - Sets state back to IDLE
5. **Frontend** displays:
   - Event log shows: "CODEX: It's 72°F and sunny..."
   - Reply Options panel shows 3 clickable buttons
6. **User clicks** "Show forecast"
7. **Frontend** → POST to `/api/reply` with `{"reply": "Show forecast"}`
8. **Backend** continues conversation flow

---

## 5. Test IDs for Automation

All interactive elements have `data-testid` attributes:

**Codex Interface:**
- `input-codex` - Main textarea
- `button-codex-submit` - TRANSMIT button
- `button-initialize` - INIT button
- `button-gaming-toggle` - GAME/GMG toggle
- `button-shutdown` - EXIT button

**Reply Options Panel:**
- `button-reply-option-0` - First option
- `button-reply-option-1` - Second option
- `button-reply-option-{index}` - Nth option

---

## 6. Complete API Reference

### Codex Endpoints

| Method | Endpoint | Purpose | Request Body | Response |
|--------|----------|---------|--------------|----------|
| POST | `/api/codex` | Submit user command/query | `{input: string}` | `{status: 'ok'}` |
| POST | `/api/reply` | Submit selected reply option | `{reply: string}` | `{status: 'ok'}` |

### Existing JARVIS Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/jarvis/core-state` | Update visualization state |
| POST | `/api/jarvis/brain-status` | Update connection status |
| POST | `/api/jarvis/event` | Add event to log |
| GET | `/api/jarvis/queue` | Fetch offline queue |
| POST | `/api/jarvis/queue/clear` | Clear queue |
| DELETE | `/api/jarvis/queue/:id` | Remove queue item |
| POST | `/api/jarvis/initialize` | Initialize system |
| POST | `/api/jarvis/shutdown` | Shutdown system |
| POST | `/api/jarvis/gaming-mode` | Toggle gaming mode |

---

## 7. Visual Design

**Codex Text Entry:**
- Large textarea with Deep Void background (#050a14/80)
- Neon Cyan borders (#00f0ff/30) with glow on focus
- Roboto Mono font for code/command aesthetic
- Control buttons in horizontal flex row
- Visual hint: "Ctrl+Enter to submit" (bottom right)

**Reply Options Panel:**
- Mirrors Queue panel styling
- Numbered buttons with cyan theme
- Hover effects: border brightens to cyan-400, shadow glow appears
- Full-width buttons with left-aligned text
- Scrollable for multiple options

---

## 8. File Locations

| Component | File Path |
|-----------|-----------|
| Main HUD Component | `client/src/pages/jarvis-hud.tsx` |
| Backend Routes | `server/routes.ts` |
| WebSocket Server | `server/index.ts` |
| API Types/Schema | `shared/schema.ts` |
| Documentation | `replit.md` |
| Integration Guide | `JARVIS_INTEGRATION.md` |

---

## 9. Development Tips

1. **State Management**: Codex and Reply Options are independent - you can use one without the other
2. **Error Handling**: Both endpoints handle network errors gracefully on frontend
3. **Clearing Reply Options**: Send empty array `{type: 'updateReplyOptions', options: []}` to hide panel
4. **Multi-turn Conversations**: Use reply options to guide users through conversational flows
5. **Event Log Integration**: Always log Codex interactions to event stream for debugging

---

## 10. Next Steps

1. Implement `/api/codex` handler in your Python backend
2. Implement `/api/reply` handler in your Python backend
3. Add WebSocket message type `updateReplyOptions` to your broadcast system
4. Test conversational flows with your AI/LLM integration
5. Configure reply options based on conversation context

---

## Support Files

- **JARVIS_INTEGRATION.md** - Original backend integration guide
- **DEPLOYMENT.md** - Raspberry Pi deployment instructions
- **replit.md** - Complete system architecture documentation

For questions about the original WebSocket protocol and backend integration, see `JARVIS_INTEGRATION.md`.
