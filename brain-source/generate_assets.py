#!/usr/bin/env python3
"""
Golden Voice Asset Generator
ONE-TIME USE SCRIPT - Generate MP3s using OpenAI fable voice
before switching to Ollama

Run this once, then archive.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load environment for OpenAI API key
load_dotenv()

def generate_golden_assets():
    """Generate the 4 critical voice assets using OpenAI fable voice"""
    
    print("=" * 60)
    print("🎙️  GOLDEN VOICE ASSET GENERATOR")
    print("=" * 60)
    print("Using OpenAI TTS (model: tts-1, voice: fable)")
    print("Generating assets before Ollama migration...\n")
    
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Asset definitions
    assets = {
        'offline.mp3': "Sir, I require a connection to the neural interface. I have added your request to the queue.",
        'boot_up.mp3': "Systems online. Attempting to reach the mainframe.",
        'gaming_mode.mp3': "Gaming protocol engaged. Neural link paused.",
        'error.mp3': "I am unable to process that request locally."
    }
    
    # Output directory (backup on PC first)
    output_dir = Path.home() / 'jarvis' / 'golden_assets'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Output directory: {output_dir}\n")
    
    # Generate each asset
    for filename, text in assets.items():
        print(f"Generating: {filename}")
        print(f"  Text: '{text}'")
        
        try:
            # Generate audio using OpenAI TTS
            response = client.audio.speech.create(
                model="tts-1",
                voice="fable",
                input=text
            )
            
            # Save MP3
            output_path = output_dir / filename
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            file_size = output_path.stat().st_size
            print(f"  ✅ Saved: {output_path} ({file_size:,} bytes)\n")
            
        except Exception as e:
            print(f"  ❌ Error: {e}\n")
            return False
    
    print("=" * 60)
    print("✅ GOLDEN ASSETS GENERATED SUCCESSFULLY")
    print("=" * 60)
    print(f"\nAssets saved to: {output_dir}")
    print("\nNext steps:")
    print("1. Transfer these to Pi: /home/spencer/jarvis/assets/audio/")
    print("2. Backup these files (they cannot be regenerated after API switch)")
    print("3. Proceed with Ollama installation")
    
    return True


if __name__ == '__main__':
    success = generate_golden_assets()
    sys.exit(0 if success else 1)
