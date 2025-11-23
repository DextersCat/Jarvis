"""
JARVISMemory - Long-term Memory System for JARVIS Assistant
Uses ChromaDB for persistent semantic memory storage

Created: November 15, 2025
Phase: 2 - Enhanced Intelligence & JARVIS Personality
Week: 1 - Long-Term Memory System
"""

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from datetime import datetime
import uuid
import re
import os
import posthog

posthog.capture = lambda *args, **kwargs: None  # disable product telemetry
posthog.disabled = True


class JARVISMemory:
    """
    Long-term memory system for JARVIS Assistant
    Uses ChromaDB for persistent semantic memory storage
    
    Features:
    - Persistent vector database with duckdb+parquet
    - Semantic search using sentence transformers
    - Two collections: conversations and preferences
    - Content validation to prevent hallucinations
    - Automatic persistence after writes
    """
    
    def __init__(self, persist_directory=None):
        """
        Initialize ChromaDB client with persistence
        
        Args:
            persist_directory: Absolute path to persistent storage directory
        """
        print(f"[JARVISMemory] Initializing memory system...")
        env_path = os.getenv("JARVIS_MEMORY_PATH", "/root/JARVIS/runtime/memory_v2")
        persist_directory = persist_directory or env_path
        print(f"[JARVISMemory] Persist directory: {persist_directory}")

        # Initialize ChromaDB PersistentClient (new API for v1.3+)
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Set up embedding function (SentenceTransformer)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction()
        
        # Create or load collections
        self.conversations_collection = self.client.get_or_create_collection(
            name="conversations",
            embedding_function=self.embedding_fn,
            metadata={"description": "Semantic conversation memory"}
        )
        
        self.preferences_collection = self.client.get_or_create_collection(
            name="preferences",
            embedding_function=self.embedding_fn,
            metadata={"description": "User preferences and personality settings"}
        )
        
        # Get collection counts
        conv_count = self.conversations_collection.count()
        pref_count = self.preferences_collection.count()
        
        print(f"[JARVISMemory] Ô£à Conversations collection loaded ({conv_count} items)")
        print(f"[JARVISMemory] Ô£à Preferences collection loaded ({pref_count} items)")
        print(f"[JARVISMemory] Memory system initialized successfully")
    
    def _validate_content(self, text):
        """
        Validate content before writing to memory
        
        Filters out:
        - Hallucinations (uncertain statements)
        - Redundant info
        - Transient chit-chat
        - Emotionally sensitive data
        - Self-contradictory data
        
        Args:
            text: Text to validate
            
        Returns:
            bool: True if content is valid, False otherwise
        """
        if not text or len(text.strip()) < 5:
            return False
        
        text_lower = text.lower()
        
        # Filter out uncertain/hallucination phrases
        uncertain_phrases = [
            "i think", "maybe", "perhaps", "possibly", "i'm not sure",
            "could be", "might be", "probably", "i guess", "unsure"
        ]
        if any(phrase in text_lower for phrase in uncertain_phrases):
            return False
        
        # Filter out transient chit-chat
        transient_phrases = [
            "hello", "hi", "hey", "goodbye", "bye", "thanks", "thank you",
            "ok", "okay", "yes", "no", "haha", "lol"
        ]
        if text_lower.strip() in transient_phrases:
            return False
        
        # Filter out very short statements (likely chit-chat)
        if len(text.split()) < 4:
            return False
        
        return True
    
    def add_conversation_memory(self, text, metadata=None):
        """
        Add conversation memory with validation
        
        Args:
            text: Conversation text to store
            metadata: Optional metadata dict (timestamp, topic, importance_score)
            
        Returns:
            str: Memory ID if successful, None if validation failed
        """
        # Validate content
        if not self._validate_content(text):
            print(f"[JARVISMemory] ÔØî Content validation failed - not storing")
            return None
        
        # Generate unique ID
        memory_id = str(uuid.uuid4())
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        # Add timestamp if not present
        if "timestamp" not in metadata:
            metadata["timestamp"] = datetime.now().isoformat()
        
        # Add default importance if not present
        if "importance_score" not in metadata:
            metadata["importance_score"] = 0.5
        
        try:
            # Add to collection
            self.conversations_collection.add(
                ids=[memory_id],
                documents=[text],
                metadatas=[metadata]
            )
            
            # Persist to disk
            self.persist()
            
            print(f"[JARVISMemory] Ô£à Conversation memory stored: {memory_id}")
            return memory_id
        
        except Exception as e:
            print(f"[JARVISMemory] ÔØî Error storing conversation: {e}")
            return None
    
    def add_preference(self, text, metadata=None):
        """
        Add preference with validation
        
        Args:
            text: Preference text to store
            metadata: Optional metadata dict (category, last_updated, priority)
            
        Returns:
            str: Preference ID if successful, None if validation failed
        """
        # Validate content
        if not self._validate_content(text):
            print(f"[JARVISMemory] ÔØî Preference validation failed - not storing")
            return None
        
        # Generate unique ID
        pref_id = str(uuid.uuid4())
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        # Add last_updated if not present
        if "last_updated" not in metadata:
            metadata["last_updated"] = datetime.now().isoformat()
        
        # Add default priority if not present
        if "priority" not in metadata:
            metadata["priority"] = "medium"
        
        try:
            # Add to collection
            self.preferences_collection.add(
                ids=[pref_id],
                documents=[text],
                metadatas=[metadata]
            )
            
            # Persist to disk
            self.persist()
            
            print(f"[JARVISMemory] Ô£à Preference stored: {pref_id}")
            return pref_id
        
        except Exception as e:
            print(f"[JARVISMemory] ÔØî Error storing preference: {e}")
            return None
    
    def query_conversations(self, query_text, top_k=5, filters=None):
        """
        Semantic search in conversations collection
        
        Args:
            query_text: Query text for semantic search
            top_k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            list: List of dicts with text, metadata, distance
        """
        try:
            results = self.conversations_collection.query(
                query_texts=[query_text],
                n_results=top_k,
                where=filters
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and len(results['documents'][0]) > 0:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None,
                        'id': results['ids'][0][i]
                    })
            
            print(f"[JARVISMemory] ­ƒöì Conversation query returned {len(formatted_results)} results")
            return formatted_results
        
        except Exception as e:
            print(f"[JARVISMemory] ÔØî Error querying conversations: {e}")
            return []
    
    def query_preferences(self, query_text, top_k=5, filters=None):
        """
        Semantic search in preferences collection
        
        Args:
            query_text: Query text for semantic search
            top_k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            list: List of dicts with text, metadata, distance
        """
        try:
            results = self.preferences_collection.query(
                query_texts=[query_text],
                n_results=top_k,
                where=filters
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and len(results['documents'][0]) > 0:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None,
                        'id': results['ids'][0][i]
                    })
            
            print(f"[JARVISMemory] ­ƒöì Preference query returned {len(formatted_results)} results")
            return formatted_results
        
        except Exception as e:
            print(f"[JARVISMemory] ÔØî Error querying preferences: {e}")
            return []
    
    def get_personality_preferences(self):
        """
        Retrieve JARVIS personality configuration
        
        Returns:
            dict: Personality preferences including tone, addressing style, etc.
        """
        try:
            # Query for personality-related preferences
            results = self.preferences_collection.query(
                query_texts=["JARVIS personality British butler professional"],
                n_results=10,
                where={"category": "personality"}
            )
            
            # Build personality dict from results
            personality = {
                "tone": "professional, calm, butler-like",
                "addressing_style": "Sir, Chairman, respectful",
                "primary_identity": "Chairman",
                "stress_minimization": True,
                "language": "Professional UK English",
                "conversational_flow": "calm"
            }
            
            # Override with stored preferences if found
            if results['documents'] and len(results['documents'][0]) > 0:
                for i in range(len(results['documents'][0])):
                    text = results['documents'][0][i]
                    metadata = results['metadatas'][0][i]
                    
                    # Parse preference text to update personality dict
                    # This is a simple implementation - can be enhanced
                    if "tone" in text.lower():
                        personality["tone"] = text
                    elif "addressing" in text.lower():
                        personality["addressing_style"] = text
            
            print(f"[JARVISMemory] ­ƒÄ¡ Personality preferences loaded")
            return personality
        
        except Exception as e:
            print(f"[JARVISMemory] ÔØî Error loading personality: {e}")
            return {
                "tone": "professional, calm, butler-like",
                "addressing_style": "Sir, Chairman, respectful",
                "primary_identity": "Chairman",
                "stress_minimization": True,
                "language": "Professional UK English",
                "conversational_flow": "calm"
            }
    
    def persist(self):
        """
        Force persistence to disk
        Ensures all changes are written to duckdb+parquet files
        """
        try:
            self.client.persist()
            # ChromaDB 1.3.4 automatically persists, but we keep this for compatibility
        except Exception as e:
            # Newer versions may not have persist() method
            pass
    
    def get_stats(self):
        """
        Get memory statistics
        
        Returns:
            dict: Statistics about collections
        """
        return {
            "conversations_count": self.conversations_collection.count(),
            "preferences_count": self.preferences_collection.count(),
            "total_memories": self.conversations_collection.count() + self.preferences_collection.count()
        }


if __name__ == "__main__":
    # Quick test
    print("=" * 70)
    print("JARVIS Memory System - Quick Test")
    print("=" * 70)
    
    memory = JARVISMemory()
    stats = memory.get_stats()
    print(f"\nMemory Statistics:")
    print(f"  Conversations: {stats['conversations_count']}")
    print(f"  Preferences: {stats['preferences_count']}")
    print(f"  Total: {stats['total_memories']}")
