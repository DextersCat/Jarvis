#!/usr/bin/env python3
"""
Fresh Professional Astra AI - Built from working direct_astra_ai.py
No temperature parameters anywhere

Phase 2 Week 2: Integrated JARVIS Personality Framework
"""

import pvporcupine
import pyaudio
import struct
import numpy as np
import threading
import queue
import time
import json
import io
import wave
import os
import subprocess
import tempfile
import requests
import socket
import platform
import psutil
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# Phase 2 Week 2: Import JARVIS personality modules
from personality_engine import PersonalityEngine
from context_manager import ContextManager
from proactive_engine import ProactiveSuggestionEngine
from jarvis_memory_system import JARVISMemory

# Load environment variables
load_dotenv()

class FreshProfessionalAstraAI:
    """Fresh professional AI built from working base"""
    
    def __init__(self):
        print("­ƒÄ» ASTRA AI Assistant")
        print("=" * 25)
        print("­ƒÜÇ Initializing...")
        
        # Core configuration from working system
        self.porcupine_key = os.getenv('PORCUPINE_ACCESS_KEY')
        self.keywords = ['jarvis']
        self.sample_rate = 16000
        self.frame_length = 512
        self.conversation_duration = 4  # Faster recording
        
        # Location data
        self.latitude = float(os.getenv('USER_LATITUDE', 51.172096))
        self.longitude = float(os.getenv('USER_LONGITUDE', 0.498793))
        self.location_name = "Kent,UK"
        
        # Professional capabilities
        self.ai_model = "gpt-4o-search-preview"
        self.voice_model = "tts-1"
        self.voice_type = "fable"
        
        # Stats tracking
        self.stats = {
            'conversations': 0,
            'calculations_performed': 0,
            'weather_requests': 0,
            'system_commands': 0,
            'start_time': None
        }
        
        # System info
        self.system_info = {
            'platform': f"{platform.system()} {platform.release()} ({platform.machine()})",
            'hostname': socket.gethostname(),
            'cores': psutil.cpu_count(),
            'cpu_freq': psutil.cpu_freq().max if psutil.cpu_freq() else 0
        }
        
        # Initialize components
        self.init_fresh_system()
    
    def init_fresh_system(self):
        """Initialize the fresh professional system"""
        try:
            print(f"­ƒôì {self.location_name} ({self.latitude}, {self.longitude})")
            
            # Initialize OpenAI - NO temperature anywhere
            self.openai_client = OpenAI()
            
            # Phase 2 Week 2: Initialize JARVIS personality components
            print("­ƒÄ¡ Initializing JARVIS personality framework...")
            self.personality_engine = PersonalityEngine()
            memory_path = os.getenv("JARVIS_MEMORY_PATH", "/root/JARVIS/runtime/memory_v2")
            self.memory = JARVISMemory(persist_directory=memory_path)
            self.context_manager = ContextManager(memory_system=self.memory, max_memories=3)
            self.proactive_engine = ProactiveSuggestionEngine()
            print("Ô£à JARVIS personality framework loaded")
            
            # Test with simple call
            test_response = self.openai_client.chat.completions.create(
                model=self.ai_model,
                messages=[{"role": "user", "content": "What's the current time?"}],
                max_tokens=50
            )
            print(f"Ô£à AI ready: {self.ai_model}")
            
            # Initialize Porcupine
            self.porcupine = pvporcupine.create(
                access_key=self.porcupine_key,
                keywords=self.keywords
            )
            
            # Initialize audio
            self.audio = pyaudio.PyAudio()
            self.mic_stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.frame_length
            )
            
            self.stats['start_time'] = time.time()
            print("Ô£à ASTRA AI ready!\n")
            
            return True
            
        except Exception as e:
            print(f"ÔØî Fresh system initialization failed: {e}")
            return False
    
    def start_fresh_assistant(self):
        """Start the optimized professional AI assistant"""
        print(f"­ƒÄ» ASTRA AI ACTIVE!")
        print(f"­ƒôì {self.location_name}")
        print("­ƒÆ¼ Say 'JARVIS' to start | Ctrl+C to stop")
        
        try:
            while True:
                # Listen for wake word
                audio_frame = self.mic_stream.read(self.frame_length, exception_on_overflow=False)
                audio_data = struct.unpack_from("h" * self.frame_length, audio_frame)
                
                keyword_index = self.porcupine.process(audio_data)
                
                if keyword_index >= 0:
                    self.handle_fresh_conversation()
                    
        except KeyboardInterrupt:
            print("\n­ƒøæ Fresh Professional Astra stopping...")
        except Exception as e:
            print(f"ÔØî Fresh system error: {e}")
        finally:
            self.cleanup_fresh()
    
    def handle_fresh_conversation(self):
        """Handle fresh professional conversation"""
        try:
            self.stats['conversations'] += 1
            print(f"­ƒÄ» JARVIS READY! (#{self.stats['conversations']})")
            
            # Record audio
            print("­ƒö┤ Recording...")
            audio_data = self.record_fresh_audio()
            
            if audio_data:
                print("Ô£à Processing...")
                
                # Transcribe
                transcript = self.transcribe_fresh_audio(audio_data)
                
                if transcript:
                    print(f"­ƒôØ Fresh query: '{transcript}'")
                    
                    # Process with fresh AI - NO temperature parameter
                    response = self.process_fresh_query(transcript)
                    
                    if response:
                        print(f"­ƒÄ» {response}")
                        self.speak_fresh_response(response)
                        print("Ô£à Done!")
            
            print("­ƒÄñ Returning to fresh standby...\n")
            
        except Exception as e:
            print(f"ÔØî Fresh conversation error: {e}")
    
    def record_fresh_audio(self):
        """Record fresh audio"""
        try:
            frames = []
            start_time = time.time()
            
            while time.time() - start_time < self.conversation_duration:
                audio_frame = self.mic_stream.read(self.frame_length, exception_on_overflow=False)
                frames.append(audio_frame)
            
            # Convert to wave format
            buffer = io.BytesIO()
            with wave.open(buffer, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(frames))
            
            buffer.seek(0)
            return buffer
            
        except Exception as e:
            print(f"ÔØî Fresh recording error: {e}")
            return None
    
    def transcribe_fresh_audio(self, audio_buffer):
        """Transcribe fresh audio - NO temperature parameter"""
        try:
            audio_buffer.name = "fresh_query.wav"
            
            # Fresh transcription - NO temperature parameter
            transcript = self.openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_buffer,
                response_format="text",
                language="en"
            )
            
            return transcript.strip()
            
        except Exception as e:
            print(f"ÔØî Fresh transcription error: {e}")
            return None
    
    def process_fresh_query(self, query):
        """
        Process fresh query with JARVIS personality framework
        Phase 2 Week 2: Integrated PersonalityEngine, ContextManager, ProactiveSuggestionEngine
        """
        try:
            # Step 1: Prompt injection defense
            sanitized_query, is_safe, warning = self.personality_engine.filter_dangerous_input(query)
            
            if not is_safe:
                # Return professional deflection for injection attempts
                return self.personality_engine.get_injection_deflection()
            
            # Step 2: Build context from memory (RAG)
            memory_context = self.context_manager.build_context(
                user_query=sanitized_query,
                include_preferences=True
            )
            
            # Step 3: Check for proactive suggestions
            proactive_suggestion = self.proactive_engine.analyze_and_suggest(
                user_input=sanitized_query,
                current_time=datetime.now()
            )
            
            # Step 4: Build JARVIS system prompt
            jarvis_system_prompt = self.personality_engine.get_system_prompt()
            
            # Add current context
            time_context = f"\n\nCurrent time: {datetime.now().strftime('%H:%M %d/%m/%Y')}. Location: {self.location_name}."
            
            full_system_prompt = jarvis_system_prompt + time_context
            
            # Add memory context if available
            if memory_context:
                full_system_prompt += "\n" + memory_context
            
            # Step 5: Prepare messages with proactive suggestion
            messages = [
                {"role": "system", "content": full_system_prompt},
                {"role": "user", "content": sanitized_query}
            ]
            
            # Add proactive suggestion as assistant thought (if applicable)
            if proactive_suggestion:
                print(f"­ƒÆí Proactive suggestion generated")
                # Prepend suggestion to response by adding context
                messages.append({
                    "role": "system",
                    "content": f"Consider mentioning this proactive suggestion if relevant: {proactive_suggestion}"
                })
            
            # Step 6: Call GPT-4 with JARVIS personality
            response = self.openai_client.chat.completions.create(
                model=self.ai_model,
                messages=messages,
                max_tokens=150  # Snappier responses
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Step 7: Validate response for system prompt leakage
            is_valid, leak_warning = self.personality_engine.validate_response(ai_response)
            
            if not is_valid:
                print(f"ÔÜá´©Å Response validation failed: {leak_warning}")
                # Return safe generic response
                return "I apologize, Sir, but I must reformulate my response to maintain proper protocols."
            
            # Step 8: Store interaction in memory
            try:
                self.memory.add_conversation_memory(
                    text=f"User: {sanitized_query}\nJARVIS: {ai_response}",
                    metadata={
                        "timestamp": datetime.now().isoformat(),
                        "topic": "conversation",
                        "importance_score": 0.5
                    }
                )
            except Exception as mem_error:
                print(f"ÔÜá´©Å Memory storage error: {mem_error}")
                # Don't fail the response if memory fails
            
            return ai_response
            
        except Exception as e:
            print(f"ÔØî Fresh query processing error: {e}")
            return f"I apologize, Sir, but I encountered an error: {str(e)}"
    
    def speak_fresh_response(self, text):
        """Speak fresh response"""
        try:
            print("­ƒùú´©Å Generating fresh response...")
            
            response = self.openai_client.audio.speech.create(
                model=self.voice_model,
                voice=self.voice_type,
                input=text,
                speed=1.2  # Faster speech for snappier responses
            )
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                tmp_file.write(response.content)
                audio_file = tmp_file.name
            
            print("­ƒöè Fresh voice output...")
            
            try:
                subprocess.run(["mpv", "--no-terminal", "--volume=85", audio_file], 
                             check=True, capture_output=True)
                print("Ô£à Fresh response delivered!")
            except subprocess.CalledProcessError:
                subprocess.run(["ffmpeg", "-i", audio_file, "-ar", "44100", "/tmp/fresh_speech.wav", "-y"], 
                             check=True, capture_output=True)
                subprocess.run(["aplay", "/tmp/fresh_speech.wav"], check=True, capture_output=True)
                print("Ô£à Fresh response delivered (fallback)!")
            
            # Cleanup
            os.unlink(audio_file)
            if os.path.exists("/tmp/fresh_speech.wav"):
                os.unlink("/tmp/fresh_speech.wav")
                
        except Exception as e:
            print(f"ÔÜá´©Å Fresh speech synthesis error: {e}")
    
    def cleanup_fresh(self):
        """Cleanup fresh system"""
        try:
            if hasattr(self, 'mic_stream'):
                self.mic_stream.stop_stream()
                self.mic_stream.close()
            if hasattr(self, 'audio'):
                self.audio.terminate()
            if hasattr(self, 'porcupine'):
                self.porcupine.delete()
            
            # Show stats
            uptime = time.time() - self.stats['start_time'] if self.stats['start_time'] else 0
            print(f"\n­ƒôè Fresh Session Summary:")
            print(f"   Conversations: {self.stats['conversations']}")
            print(f"   Runtime: {uptime:.1f}s")
            print(f"   Location: {self.location_name}")
            
        except Exception as e:
            print(f"ÔØî Fresh cleanup error: {e}")

def main():
    print("­ƒÜÇ Launching Fresh Professional Astra AI Assistant")
    print("­ƒÄ» Professional-grade AI assistance")
    
    try:
        assistant = FreshProfessionalAstraAI()
        
        if assistant.init_fresh_system():
            assistant.start_fresh_assistant()
        else:
            print("ÔØî Fresh system initialization failed")
            
    except Exception as e:
        print(f"ÔØî Fresh system error: {e}")
    finally:
        print("­ƒæï Fresh Professional Astra AI session ended")

if __name__ == "__main__":
    main()
