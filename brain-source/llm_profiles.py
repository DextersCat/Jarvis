"""
LLM profile loader for Jarvis.
Reads YAML profiles and selects one by name (env JARVIS_LLM_PROFILE).
"""

import os
from pathlib import Path
from typing import Dict

import yaml

DEFAULT_PROFILE = "realtime_light"
PROFILES_PATH = Path(__file__).resolve().parent.parent / "config" / "llm_profiles.yaml"


def load_profiles() -> Dict[str, dict]:
    if not PROFILES_PATH.exists():
        return {}
    try:
        data = yaml.safe_load(PROFILES_PATH.read_text(encoding="utf-8")) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def select_profile(name: str | None = None) -> dict:
    profiles = load_profiles()
    profile_name = name or os.getenv("JARVIS_LLM_PROFILE", DEFAULT_PROFILE)
    profile = profiles.get(profile_name)
    if not profile:
        # fallback to default if requested missing
        profile = profiles.get(DEFAULT_PROFILE, {})
    return {
        "name": profile_name,
        "model": profile.get("model", "llama3"),
        "base_url": profile.get("base_url"),
        "api_key": profile.get("api_key"),
        "description": profile.get("description", ""),
    }
