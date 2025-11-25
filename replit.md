# Stark Industries Jarvis HUD

## Overview

The Stark Industries Jarvis HUD is a premium web-based interface inspired by Tony Stark's "Iron Man" JARVIS system. Featuring a futuristic holographic aesthetic with glass morphism, glowing neon cyan accents, and a pulsing AI core visualization, this HUD provides real-time monitoring for an AI assistant system running on a Raspberry Pi 5.

The interface is optimized for fullscreen kiosk mode (1080p) with no scrollbars, creating an immersive command center experience. The system connects to a Python backend (Ai-Pi) via WebSocket for real-time state updates.

**Design Theme**: Sci-fi holographic interface with Deep Void backgrounds, Neon Cyan glows, and premium glass panels.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes (November 20, 2025)

**Complete redesign** from neural network canvas to Stark Industries aesthetic:
- New color scheme: Deep Void background (#050a14), Neon Cyan accents (#00f0ff)
- Central visualization: Animated neural network GIF with state-based color filtering
- Simplified state model to 4 states with color-coded visualization
- Added glass morphism with backdrop blur and glowing cyan borders
- Implemented dummy system metrics (CPU, RAM, Sensitivity) with animated progress bars
- Enhanced terminal-style event log with green monospace text
- Preserved WebSocket integration for Python backend connection

**Latest Update** (Neural Network GIF Integration):
- Replaced pulsing orb with animated neural network GIF
- Implemented CSS hue-rotate filters for state-specific colors
- Added mix-blend-mode 'screen' for holographic effect
- Maintained breathing animations with Framer Motion
- GIF size: 500x500px with radial glow background

## System Architecture

### Frontend Architecture

**Framework**: React 18 with TypeScript, using Vite as the build tool and development server.

**Animation Library**: Framer Motion for smooth, performant animations (pulsing orb, breathing effects, panel transitions).

**Routing**: Wouter for client-side routing (lightweight React Router alternative).

**State Management**: React hooks for local state management. Four-state system (IDLE, LISTENING, PROCESSING, SPEAKING) with automatic cycling for demo purposes. WebSocket messages from Python backend can override the demo cycle.

**UI Styling**: Tailwind CSS with custom design tokens for glass morphism, glowing effects, and Stark Industries color palette. No external CSS frameworks - pure Tailwind utilities.

**Real-time Updates**: WebSocket connection at `/jarvis-ws` for receiving state updates from Python backend. The main page (`jarvis-hud.tsx`) manages the WebSocket lifecycle with automatic reconnection (3-second retry interval) and graceful degradation when backend is offline.

**Key Design Decisions**:
- Single-page application with fullscreen layout (100vh, overflow hidden, no scrollbars)
- Clean component structure: JarvisHUD main page with PulsingOrb, SystemHealthPanel, BrainStatusPanel, and EventLogTerminal sub-components
- Framer Motion for breathing animations optimized for Raspberry Pi 5 performance
- Responsive grid layout: 3-column desktop (System Health, Central Orb, Brain Status) + bottom Event Log
- Auto-cycling demo mode (4-second intervals) that runs independently of WebSocket connection
- Glass panel system using custom Tailwind utilities (glass-panel class)

### Visual Design System

**Color Palette**:
- Deep Void Background: `#050a14` (HSL: 212, 47%, 6%)
- Neon Cyan Primary: `#00f0ff` (HSL: 184, 100%, 50%) - IDLE state
- Blue: `#0080ff` (HSL: 210, 100%, 50%) - LISTENING state
- Yellow/Amber: `#ffaa00` (HSL: 40, 100%, 50%) - PROCESSING state
- Green: `#00ff88` (HSL: 152, 100%, 50%) - SPEAKING state
- Terminal Green: `#00ff88` - Event log text

**Typography**:
- Headers/Titles: 'Orbitron' - Futuristic, geometric, tech-focused
- Body/UI: 'Rajdhani' - Clean, modern, highly readable
- Terminal/Code: 'Roboto Mono' - Monospace for technical data, timestamps, event log

**Glass Morphism System**:
- Semi-transparent dark backgrounds (rgba with 20-40% opacity)
- Backdrop blur (12-16px) for holographic glass effect
- Glowing cyan borders (1px solid with 30% opacity)
- Subtle cyan shadows (box-shadow with multiple layers)

**Animations**:
- Pulsing Orb: Continuous breathing (scale 1.0 → 1.1 → 1.0, opacity 0.8 → 1.0 → 0.8) over 2.5 seconds
- Inner Rings: Multiple concentric rings with staggered animation delays
- Connection Indicator: Green dot pulses when brain is online
- Metric Bars: Smooth width transitions with box-shadow glow
- Panel Entrance: Fade in with y-offset (opacity 0 → 1, y: 20 → 0) over 0.6s
- Event Log: Slide in from left (x: -10 → 0) over 0.2s per entry

### State System

**Four States** with automatic cycling (4-second intervals):

1. **IDLE** (Cyan #00f0ff)
   - Label: "STANDBY"
   - Orb Color: Neon cyan with cyan glow
   - Waiting for input

2. **LISTENING** (Blue #0080ff)
   - Label: "RECEIVING INPUT"
   - Orb Color: Blue with blue glow
   - Actively receiving voice/text input

3. **PROCESSING** (Yellow #ffaa00)
   - Label: "ANALYZING"
   - Orb Color: Yellow/amber with yellow glow
   - Processing request, thinking, querying AI model

4. **SPEAKING** (Green #00ff88)
   - Label: "RESPONDING"
   - Orb Color: Green with green glow
   - Generating and delivering response

**State Transition Logic**:
- Demo Mode: Auto-cycles through states every 4 seconds (IDLE → LISTENING → PROCESSING → SPEAKING → repeat)
- Production Mode: Python backend sends WebSocket messages to change state based on actual AI activity
- Smooth color transitions (0.5s duration, ease-in-out)

### Components Breakdown

**Neural Network Visualization** (Center):
- Animated neural network GIF (500x500px container)
- CSS filter effects: hue-rotate(), saturate(), brightness() based on state
- Mix-blend-mode 'screen' for holographic overlay effect
- Continuous breathing animation using Framer Motion (scale 1.0 → 1.05 → 1.0)
- Radial gradient background glow that changes color with state
- Expanding ring border animation for depth
- Smooth filter transitions (0.5s) when state changes

**State-Based Color Filters**:
- IDLE (Cyan): hue-rotate(180deg) saturate(1.5) brightness(1.2)
- LISTENING (Blue): hue-rotate(210deg) saturate(1.3) brightness(1.1)
- PROCESSING (Yellow): hue-rotate(40deg) saturate(1.8) brightness(1.3)
- SPEAKING (Green): hue-rotate(140deg) saturate(1.5) brightness(1.2)

**SystemHealthPanel** (Left Panel):
- CPU Usage: Animated progress bar (15-35% range with random updates every 2s)
- RAM Usage: Animated progress bar (35-50% range)
- Sensitivity: Animated progress bar (70-85% range)
- Uptime display (static placeholder: 14:23:47)
- All metrics use dummy data for demo purposes

**BrainStatusPanel** (Right Panel):
- Connection Status: Pulsing green indicator when online, red when offline
- Model Name: AI model identifier (default: "GPT-4o")
- Latency: Response time in milliseconds (80-180ms range, randomized)
- Neural Cores: Static display (8/8)
- Processing Units: Status display (ACTIVE)

**EventLogTerminal** (Bottom Panel):
- Terminal-style scrolling log with green monospace text
- Format: `[HH:MM:SS] MESSAGE`
- Auto-scroll to newest entries
- AnimatePresence for smooth entry/exit animations
- Custom terminal scrollbar (green theme)
- Maximum 20 visible entries, older entries removed

### Backend Architecture

**Server Framework**: Express.js running on Node.js with TypeScript.

**WebSocket Server**: ws library providing real-time bidirectional communication at `/jarvis-ws` endpoint for Python backend integration.

**Development Server**: Vite middleware integration for hot module replacement during development.

**API Structure**: RESTful endpoints at `/api/jarvis/*` that Python backend can call to update HUD state. The server broadcasts all updates to connected WebSocket clients.

**API Endpoints**:
- POST `/api/jarvis/core-state` - Update visualization state (`{state: "idle" | "listening" | "processing" | "speaking"}`)
- POST `/api/jarvis/loop-state` - Update AI-Pi loop running status
- POST `/api/jarvis/brain-status` - Update brain connection and model info (`{isOnline: boolean, modelName?: string}`)
- POST `/api/jarvis/ai-pi-status` - Update wake mode and audio timing
- POST `/api/jarvis/event` - Add events to the log (`{message: string}`)

**Key Design Decisions**:
- HTTP server created with `createServer()` to support both Express and WebSocket
- Client connection tracking using a Set to manage active WebSocket connections
- Broadcast helper function to send updates to all connected clients
- Simple REST API for Python backend to send updates without maintaining WebSocket connection
- Middleware for request logging and JSON body parsing

### WebSocket Message Protocol

**Messages from Backend to HUD**:

```javascript
// Update visualization state
{
  type: "updateCoreState",
  state: "idle" | "listening" | "processing" | "speaking"
}

// Update brain status
{
  type: "updateBrainStatus",
  isOnline: boolean,
  modelName?: string
}

// Add event to log
{
  type: "addEventLog",
  message: string
}
```

**Connection Behavior**:
- Auto-connect on page load
- Auto-reconnect on disconnect with 3-second delay
- Graceful degradation: Demo state cycling continues if WebSocket fails
- Connection events logged to terminal

### Data Storage Solutions

**Current Implementation**: In-memory storage using `MemStorage` class with Map-based user storage.

**Schema Definition**: Drizzle ORM schema defined in `shared/schema.ts` with PostgreSQL table definitions.

**Note**: Database integration is configured but not actively used by the HUD. The HUD operates purely on WebSocket/REST API communication with the Python backend.

### External Dependencies

**UI & Animation**: 
- Framer Motion for performant animations
- Radix UI primitives (for shadcn/ui component system if extended in future)
- Tailwind CSS for styling with custom design tokens

**Development Tools**:
- Replit-specific plugins: vite-plugin-runtime-error-modal, vite-plugin-cartographer, vite-plugin-dev-banner
- TypeScript for type safety
- ESBuild for production builds

**WebSocket**: ws library for real-time communication

**Fonts**: Google Fonts (Orbitron, Rajdhani, Roboto Mono) loaded via CDN import in index.css

**Python Backend Integration**: The system expects a Python backend to connect via WebSocket and send JSON messages with specific types (updateCoreState, updateBrainStatus, addEventLog) as documented in JARVIS_INTEGRATION.md.

## Testing & Quality Assurance

**Test Coverage**:
- End-to-end Playwright tests verify complete user flows
- State cycling verified to transition every 4 seconds
- All panels, metrics, and visual elements tested
- WebSocket connection and reconnection tested
- Responsive layout tested for desktop configuration

**Test IDs**:
All interactive and display elements have `data-testid` attributes for automated testing:
- `text-status-main`: Current state text (IDLE, LISTENING, etc.)
- `text-status-label`: State description (STANDBY, RECEIVING INPUT, etc.)
- `panel-system-health`, `panel-brain-status`, `panel-event-log`: Panel containers
- `metric-cpu-usage`, `metric-ram-usage`, `metric-sensitivity`: Metric displays
- `indicator-connection`: Brain connection status indicator
- `text-model-name`, `text-latency`: Brain status fields
- `log-container`: Event log scrollable container
- `event-{index}`: Individual event entries

## Performance Optimizations

**Raspberry Pi 5 Specific**:
- Framer Motion animations use GPU acceleration
- Single centralized state prevents unnecessary re-renders
- Efficient interval management with proper cleanup
- Lightweight components without heavy dependencies
- No canvas manipulation (unlike previous neural network version)
- CSS animations and transforms optimized for hardware acceleration

**Production Readiness**:
- Fullscreen kiosk mode (no scrollbars, overflow hidden)
- Optimized for 1080p displays (1920x1080)
- Minimal JavaScript bundle size
- Efficient WebSocket connection with automatic reconnection
- Graceful degradation when backend is offline

## Deployment

The application is packaged in `stark-hud-v2.tar.gz` for deployment to Raspberry Pi 5. Complete deployment instructions are in `DEPLOYMENT.md`.

**Quick Deploy**:
1. Transfer archive to Raspberry Pi
2. Extract and install dependencies (`npm install`)
3. Build for production (`npm run build`)
4. Run server (`npm start`)
5. Access at `http://localhost:5000`

**Python Integration**: See `JARVIS_INTEGRATION.md` for complete backend integration examples.
