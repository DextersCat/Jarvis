# Stark Industries HUD Design Guidelines

## Theme
Futuristic "Iron Man" style Heads-Up Display with holographic, fluid, minimal but functional aesthetic.

## Color Palette

### Primary Colors
- **Deep Void Background**: `#050a14` - The main background color, creating a dark space for holographic elements to shine
- **Neon Cyan Accent**: `#00f0ff` - Primary accent color for borders, highlights, and UI elements
- **Transparent Glass**: Semi-transparent panels with backdrop blur for that holographic feel

### State-Based Colors
The center visualization changes color based on JARVIS state:
- **IDLE**: Neon Cyan (`#00f0ff`) - Calm, waiting state
- **LISTENING**: Blue (`#0080ff`) - Active listening, receiving input
- **PROCESSING**: Yellow/Amber (`#ffaa00`) - Thinking, analyzing
- **SPEAKING**: Green (`#00ff88`) - Responding, output mode

### Supporting Colors
- **Text Primary**: `#e0f4ff` - High contrast for important information
- **Text Secondary**: `#80b8d0` - Medium contrast for labels and secondary info
- **Text Tertiary**: `#405060` - Low contrast for subtle details
- **Glass Border**: `#00f0ff` with low opacity - Glowing cyan borders on panels
- **Terminal Green**: `#00ff88` - For event log terminal aesthetic

## Typography

### Font Families
- **Headers/Display**: 'Orbitron', sans-serif - Futuristic, tech-focused
- **Body/UI**: 'Rajdhani', sans-serif - Clean, modern, readable
- **Code/Terminal**: 'Roboto Mono', monospace - For event log and technical data

### Font Sizes
- **Large Display**: 3rem+ - Center visualization labels
- **Section Headers**: 1.5rem - Panel titles
- **Body Text**: 1rem - Status indicators, labels
- **Small Text**: 0.875rem - Secondary information, timestamps

## Layout

### Grid Structure
Fullscreen kiosk mode optimized for 1080p displays (1920x1080):

```
┌─────────────┬───────────────────┬─────────────┐
│   System    │                   │    Brain    │
│   Health    │   Visualization   │   Status    │
│   Panel     │    (Pulsing Orb)  │   Panel     │
│             │                   │             │
├─────────────┴───────────────────┴─────────────┤
│           Event Log Terminal                  │
└───────────────────────────────────────────────┘
```

### Spacing
- **Panel Padding**: 1.5rem (24px)
- **Grid Gap**: 1rem (16px)
- **Section Spacing**: 1rem (16px)
- **No Scrollbars**: Interface should fit viewport exactly

## Visual Effects

### Glass Panels
All information panels should have:
- **Background**: Semi-transparent dark with `bg-card/20` or similar
- **Backdrop Filter**: `backdrop-blur-md` for glass effect
- **Border**: 1px glowing cyan border (`border-cyan-500/30`)
- **Shadow**: Subtle cyan glow (`shadow-lg shadow-cyan-500/10`)

### Animations (Framer Motion)

#### Breathing Effect
The center orb should continuously "breathe":
- **Scale**: 1.0 → 1.1 → 1.0
- **Duration**: 2-3 seconds per cycle
- **Easing**: Smooth, organic (ease-in-out)
- **Opacity**: Subtle pulse 0.8 → 1.0 → 0.8

#### Panel Entrance
Panels should fade in on load:
- **Initial**: opacity: 0, y: 20
- **Animate**: opacity: 1, y: 0
- **Duration**: 0.6s with stagger

#### State Transitions
Color changes should be smooth:
- **Duration**: 0.5s
- **Easing**: ease-in-out

### Glowing Effects
- **Borders**: Use cyan with low opacity for subtle glow
- **Active Elements**: Increase opacity/brightness on interaction
- **Orb Glow**: Radial gradient with blur for holographic feel

## Components

### Pulsing Orb (Center Visualization)
- Large circular element (300-400px)
- Radial gradient background based on current state
- Continuous breathing animation
- Optional: Inner rings or waveform overlay
- State label displayed below

### System Health Panel (Left)
Display dummy data for:
- **CPU Usage**: Percentage with animated bar
- **RAM Usage**: Percentage with animated bar  
- **Sensitivity**: Slider/value indicator
- Update values periodically for realism

### Brain Status Panel (Right)
Display:
- **Connection Status**: Online/Offline with indicator dot
- **Model Name**: Current AI model being used
- **Response Time**: Average latency

### Event Log Terminal (Bottom)
- Scrolling text display with terminal aesthetic
- Green text on dark background
- Monospace font
- Auto-scroll to newest events
- Timestamp prefix for each entry
- Max height with hidden overflow

## Interactivity

### Hover States
- Slight brightness increase on panels
- Border glow intensity increases

### Click States
- Brief scale animation (0.98)
- Ripple effect optional

## Code Structure

### Preferred Approach
- Single page component with minimal sub-components
- Framer Motion for all animations
- Tailwind for 100% of styling
- Clean, readable, well-commented code

### State Management
Simple React state for:
- Current status (IDLE, LISTENING, PROCESSING, SPEAKING)
- System metrics (dummy data)
- Event log entries

## Premium Polish Checklist

✅ Glass morphism with backdrop blur  
✅ Glowing cyan borders  
✅ Smooth state color transitions  
✅ Breathing orb animation  
✅ Terminal-style event log  
✅ No scrollbars (perfect viewport fit)  
✅ Holographic aesthetic  
✅ Futuristic fonts  
✅ Responsive to state changes  
✅ Professional, expensive look
