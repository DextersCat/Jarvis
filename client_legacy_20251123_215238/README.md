# Jarvis C3 HUD (Client)

Use this document when sharing the web HUD with an external editor (e.g., Replit) so the layout and build tooling stay intact.

## Repository layout

```
client/
├── README.md          # This file
├── index.html         # Vite entry point
├── package.json       # Dependencies + scripts
├── tsconfig.json      # TypeScript config used by Vite
├── vite.config.ts     # Vite/Tailwind configuration
├── tailwind.config.ts # Styling config
├── postcss.config.js  # Tailwind/PostCSS pipeline
├── src/               # React components + routes (edit these for layout changes)
└── public/            # Static assets (favicons, fonts, etc.)
```

Everything listed above must be present when uploading to Replit. The HUD depends on Tailwind, Vite, React, and the existing TypeScript tooling.

## Getting started on Replit

1. Create a new **Node.js** Replit.
2. Upload the entire `client/` directory (including `package.json`, `package-lock.json`, configs, `src/`, and `public/`).
3. Run `npm install` once to pull dependencies.
4. Start the dev server with `npm run dev -- --host 0.0.0.0 --port 5173` so Replit exposes the preview port.
5. The HUD expects the Pi API at `http://<pi-ip>:8766`. When working remotely, you can mock `/api/*` endpoints or tunnel to the Pi.

## What editors should (and shouldn’t) change

- **OK to edit:**
  - Components and pages under `src/` (React/TypeScript files)
  - Tailwind classes or styles in `src/`/`public/`
  - Static assets added to `public/`
- **Do not edit without coordination:**
  - API route paths (`/api/state`, `/api/events`, etc.).  The HUD polls those exact endpoints.
  - Websocket/REST URLs defined in `src/lib/*` (if you change these, the Pi integration breaks).
  - Package names or build scripts in `package.json` unless you tell Codex beforehand.

## Deliverables from Replit

When layout changes are ready, export only the updated files (usually under `src/` plus any new assets). Codex on the Pi will drop them back into `client/` and run `npm run build` as usual.

If additional dependencies were added, include the updated `package.json`/`package-lock.json` so we can keep versions in sync.
