import os
import sys
from pathlib import Path
from openai import OpenAI


def load_env():
    primary = Path("/root/JARVIS/config/.env")
    fallback = Path.home() / "JARVIS" / "config" / ".env"
    env_file = primary if primary.exists() else fallback

    if not env_file.exists():
        print(f"[AssetGen] Env file not found: {env_file}")
        return

    for line in env_file.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ[key] = value


def main():
    load_env()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("[AssetGen] OPENAI_API_KEY not found in JARVIS .env file.")
        sys.exit(1)

    client = OpenAI()

    out_dir = "/root/JARVIS/voice_assets"
    os.makedirs(out_dir, exist_ok=True)

    lines = {
        "offline.mp3": (
            "Sir, the neural network link has been severed. Attempting reconnection."
        ),
        "offline_queued.mp3": (
            "Sir, the neural network link has been severed. "
            "I have added your request to the local queue and will process it "
            "when the mainframe is back online."
        ),
        "mainframe_online.mp3": (
            "Neural connection restored. Mainframe online, Sir."
        ),
        "queue_added.mp3": (
            "Request stored, Sir."
        ),
        "queue_purged.mp3": (
            "All queued requests have been cleared, Sir."
        ),
        "good_morning.mp3": (
            "Good morning, Sir."
        ),
        "welcome_back.mp3": (
            "Welcome back, Sir."
        ),
        "gaming_on.mp3": (
            "Gaming mode enabled. Wake word and voice input are now paused, Sir."
        ),
        "gaming_off.mp3": (
            "Gaming mode disabled. Voice control is now available again, Sir."
        ),
        "shutdown.mp3": (
            "System shutdown in progress, Sir."
        ),
    }

    print(f"[AssetGen] Output directory: {out_dir}")
    for filename, text in lines.items():
        path = os.path.join(out_dir, filename)
        print(f"[AssetGen] Generating {filename}...")
        with client.audio.speech.with_streaming_response.create(
            model="tts-1",
            voice="fable",
            input=text,
            response_format="mp3",
        ) as response:
            response.stream_to_file(path)
        print(f"[AssetGen] Saved {path}")

    print("[AssetGen] Done.")


if __name__ == "__main__":
    main()
