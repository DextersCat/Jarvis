#!/usr/bin/env python3
"""
LLM profile diagnostic: exercise each configured profile with a short prompt.
Logs model, latency, and response length.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path

from openai import OpenAI

import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
BS = ROOT / "brain-source"
if str(BS) not in sys.path:
    sys.path.insert(0, str(BS))

from llm_profiles import load_profiles, select_profile

LOG_DIR = Path("/root/JARVIS/runtime/logs/llm")
LOG_DIR.mkdir(parents=True, exist_ok=True)


def run_check(profile_name: str) -> dict:
    profile = select_profile(profile_name)
    client = OpenAI(
        base_url=profile.get("base_url"),
        api_key=profile.get("api_key"),
    )
    prompt = "Summarise: Jarvis brain diagnostic. Keep it to 1-2 sentences."
    started = time.time()
    try:
        completion = client.chat.completions.create(
            model=profile.get("model"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
        )
        elapsed = time.time() - started
        content = completion.choices[0].message.content or ""
        return {
            "profile": profile_name,
            "model": profile.get("model"),
            "status": "PASS",
            "latency_sec": round(elapsed, 2),
            "response_len": len(content),
        }
    except Exception as exc:  # noqa: BLE001
        elapsed = time.time() - started
        return {
            "profile": profile_name,
            "model": profile.get("model"),
            "status": "FAIL",
            "latency_sec": round(elapsed, 2),
            "error": repr(exc),
        }


def main():
    profiles = load_profiles() or {}
    if not profiles:
        print("No profiles found; ensure config/llm_profiles.yaml exists.")
        return 1
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"llm_check_{timestamp}.log"
    results = []
    for name in profiles:
        res = run_check(name)
        results.append(res)
        print(json.dumps(res, indent=2))
    log_path.write_text(json.dumps(results, indent=2))
    print(f"Results logged to {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
