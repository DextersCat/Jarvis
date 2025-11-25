# Stark Industries Jarvis HUD

## Overview

The Stark Industries Jarvis HUD is a premium, web-based interface inspired by Tony Stark's "Iron Man" JARVIS system. It features a futuristic holographic aesthetic with glass morphism, neon cyan accents, and an animated neural network visualization. This HUD provides real-time monitoring for an AI assistant system running on a Raspberry Pi 5.

Optimized for fullscreen kiosk mode at 2560x1440 resolution, the interface creates an immersive command center experience. It connects to a Python backend (Ai-Pi) via WebSocket for real-time state updates and includes Codex integration for conversational AI interactions. The design theme focuses on Sci-fi holographic elements with Deep Void backgrounds, Neon Cyan glows, and premium glass panels.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

The frontend is built with **React 18** and **TypeScript**, using **Vite** for development and bundling. **Framer Motion** handles smooth, performant animations, and **Wouter** provides lightweight client-side routing. State management relies on React hooks, supporting a four-state system (IDLE, LISTENING, PROCESSING, SPEAKING) that can be controlled by WebSocket messages from the Python backend. UI styling is achieved using **Tailwind CSS** with custom design tokens for the holographic and glass morphism effects. Real-time updates are managed via a **WebSocket connection** at `/jarvis-ws` with automatic reconnection logic.

The application is a single-page interface optimized for a 2560x1440 resolution, featuring a 3-column grid layout (420px | flexible | 420px) with an 8px gap. Key components include `SystemHealthPanel`, `NeuralVisualization`, `BrainStatusPanel`, `QueuePanel`, `ReplyOptionsPanel`, `EventLog`, and `CodexInterface`. A demo mode allows the HUD to cycle through states independently of the WebSocket connection.

### Visual Design System

The visual design is characterized by a **Deep Void background** (`#050a14`) and **Neon Cyan primary accents** (`#00f0ff`). State changes are indicated by distinct colors: Blue for LISTENING, Yellow/Amber for PROCESSING, and Green for SPEAKING. Typography uses 'Orbitron' for headers, 'Rajdhani' for body text, and 'Roboto Mono' for terminal displays. **Glass morphism** effects are implemented with semi-transparent backgrounds, backdrop blur, and glowing cyan borders. Animations like pulsing orbs, spinning rings, and smooth metric transitions enhance the futuristic feel.

### State System

The system operates on four core states: **IDLE** (Cyan, "STANDBY"), **LISTENING** (Blue, "RECEIVING INPUT"), **PROCESSING** (Yellow/Amber, "ANALYZING"), and **SPEAKING** (Green, "RESPONDING"). These states define the visualization's color and behavior. State transitions are either auto-cycled every 4 seconds in demo mode or driven by WebSocket messages from the Python backend in production, with smooth 0.5s color transitions.

### Components

-   **Neural Network Visualization**: Central animated GIF (`/assets/neural.gif`) with state-based CSS filter effects (hue-rotate, saturate, brightness) and mix-blend-mode 'screen' for a holographic overlay. Features breathing animations and concentric spinning rings.
-   **SystemHealthPanel** (Left column, top): Displays dummy CPU, RAM, and Sensitivity usage with animated progress bars.
-   **ReplyOptionsPanel** (Left column, bottom): Presents conversational reply choices for Codex interactions, sending POST requests to `/api/reply`. Mirrors the Queue panel layout.
-   **BrainStatusPanel** (Right column, top): Shows connection status, model name, latency, and processing unit status.
-   **QueuePanel** (Right column, bottom): Manages offline queue items, allowing refresh and purging. Mirrors the Reply Options panel layout.
-   **EventLogTerminal** (Bottom left): A terminal-style scrollable log with cyan monospace text, auto-scrolling to new entries.
-   **CodexInterface** (Bottom right): A large textarea for command/query input to `/api/codex`, with dedicated buttons for transmit, initialize, gaming mode toggle, and shutdown.

### Backend Architecture

The backend uses **Express.js** with **Node.js** and **TypeScript**. A **WebSocket server** (`ws` library) provides real-time communication at `/jarvis-ws`. RESTful API endpoints at `/api/jarvis/*` allow the Python backend to update HUD state, which is then broadcast to connected WebSocket clients. Key API endpoints include updating core state, brain status, event logs, queue management, and submitting Codex commands or reply options.

### WebSocket Message Protocol

The Python backend communicates with the HUD using JSON messages over WebSocket. Message types include `updateCoreState` (for visualization state), `updateBrainStatus` (for online status and model info), and `addEventLog` (for terminal log entries). The system ensures auto-connection and auto-reconnection with graceful degradation, where demo state cycling continues if the WebSocket connection is lost.

### Data Storage Solutions

The current implementation uses in-memory storage. While Drizzle ORM schema for PostgreSQL is defined, database integration is not actively used by the HUD; it operates purely on WebSocket/REST API communication.

## External Dependencies

-   **UI & Animation**: Framer Motion, Tailwind CSS
-   **Development Tools**: Vite, TypeScript, ESBuild
-   **Real-time Communication**: `ws` library (for WebSocket server)
-   **Fonts**: Google Fonts (Orbitron, Rajdhani, Roboto Mono)
-   **Backend Integration**: Expects a Python backend (Ai-Pi) for WebSocket and REST API interactions.