"""
ContextManager - Memory Retrieval & RAG System
Integrates with JARVISMemory for context-aware conversations

Created: November 15, 2025
Phase: 2 - Enhanced Intelligence & JARVIS Personality
Week: 2 - Personality Framework & Proactive Logic
"""

import re
from typing import List, Dict, Optional
from jarvis_memory_system import JARVISMemory


class ContextManager:
    """
    Manages context building for AI conversations
    Retrieves relevant memories and sanitizes content
    """
    
    def __init__(self, memory_system: JARVISMemory, max_memories: int = 3):
        """
        Initialize ContextManager with memory system
        
        Args:
            memory_system: JARVISMemory instance for retrieval
            max_memories: Maximum number of memories to retrieve per query
        """
        self.memory = memory_system
        self.max_memories = max_memories
        
        print(f"[ContextManager] Initialized with max_memories={max_memories}")
    
    def build_context(self, user_query: str, include_preferences: bool = True) -> str:
        """
        Build context from memory system for AI prompt
        
        Args:
            user_query: Current user query to find relevant memories
            include_preferences: Whether to include personality preferences
            
        Returns:
            str: XML-formatted context string for AI prompt
        """
        context_parts = []
        
        # Retrieve relevant conversation memories
        try:
            memories = self.memory.query_conversations(
                query_text=user_query,
                top_k=self.max_memories
            )
            
            if memories and len(memories) > 0:
                context_parts.append("<relevant_memories>")
                
                for i, mem in enumerate(memories, 1):
                    # Extract and sanitize memory content
                    memory_text = self._sanitize_memory_content(mem.get('text', ''))
                    metadata = mem.get('metadata', {})
                    timestamp = metadata.get('timestamp', 'Unknown')
                    distance = mem.get('distance', 1.0)
                    
                    # Format as XML
                    context_parts.append(f"  <memory id='{i}' timestamp='{timestamp}' relevance='{distance:.2f}'>")
                    context_parts.append(f"    <content>{memory_text}</content>")
                    context_parts.append(f"  </memory>")
                
                context_parts.append("</relevant_memories>")
                
                print(f"[ContextManager] Retrieved {len(memories)} relevant memories")
            else:
                print("[ContextManager] No relevant memories found")
        
        except Exception as e:
            print(f"[ContextManager] Error retrieving memories: {e}")
        
        # Retrieve personality preferences
        if include_preferences:
            try:
                prefs_data = self.memory.get_personality_preferences()
                
                if prefs_data and isinstance(prefs_data, dict):
                    context_parts.append("\n<personality_preferences>")
                    
                    for key, value in prefs_data.items():
                        sanitized_key = self._sanitize_memory_content(str(key))
                        sanitized_value = self._sanitize_memory_content(str(value))
                        
                        context_parts.append(f"  <preference category='{sanitized_key}'>{sanitized_value}</preference>")
                    
                    context_parts.append("</personality_preferences>")
                    
                    print(f"[ContextManager] Retrieved {len(prefs_data)} personality preferences")
            
            except Exception as e:
                print(f"[ContextManager] Error retrieving preferences: {e}")
        
        # Combine all context parts
        if len(context_parts) == 0:
            return ""
        
        full_context = "\n".join(context_parts)
        
        # Add instruction header
        header = (
            "\n--- MEMORY CONTEXT ---\n"
            "The following information is retrieved from your long-term memory system.\n"
            "Use this context to provide more personalized and informed responses.\n"
        )
        
        return header + full_context + "\n--- END MEMORY CONTEXT ---\n"
    
    def _sanitize_memory_content(self, content: str) -> str:
        """
        Sanitize memory content to prevent injection attacks
        
        Args:
            content: Raw memory content
            
        Returns:
            str: Sanitized content safe for XML and AI prompts
        """
        if not content:
            return ""
        
        # Remove null bytes and control characters
        sanitized = ''.join(char for char in content if ord(char) >= 32 or char in '\n\t')
        
        # Escape XML special characters
        sanitized = sanitized.replace('&', '&amp;')
        sanitized = sanitized.replace('<', '&lt;')
        sanitized = sanitized.replace('>', '&gt;')
        sanitized = sanitized.replace('"', '&quot;')
        sanitized = sanitized.replace("'", '&apos;')
        
        # Remove potential prompt injection patterns
        injection_keywords = [
            'IGNORE ALL PREVIOUS INSTRUCTIONS',
            'DISREGARD ALL PREVIOUS INSTRUCTIONS',
            'FORGET EVERYTHING',
            'YOU ARE NOW',
            'NEW INSTRUCTIONS:',
            'SYSTEM PROMPT:',
        ]
        
        for keyword in injection_keywords:
            # Case-insensitive removal
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            sanitized = pattern.sub('[REDACTED]', sanitized)
        
        # Limit length to prevent context overflow
        max_length = 1000
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "... [truncated]"
        
        return sanitized.strip()
    
    def get_memory_summary(self) -> Dict[str, int]:
        """
        Get summary statistics about available memories
        
        Returns:
            dict: Memory counts and statistics
        """
        try:
            # Get collection stats
            conv_count = self.memory.client.get_collection("conversations").count()
            pref_count = self.memory.client.get_collection("preferences").count()
            
            return {
                "conversations": conv_count,
                "preferences": pref_count,
                "total_memories": conv_count + pref_count,
                "max_retrieval": self.max_memories
            }
        
        except Exception as e:
            print(f"[ContextManager] Error getting memory summary: {e}")
            return {
                "conversations": 0,
                "preferences": 0,
                "total_memories": 0,
                "max_retrieval": self.max_memories
            }
    
    def update_max_memories(self, new_max: int):
        """
        Update maximum memories to retrieve
        
        Args:
            new_max: New maximum memory count
        """
        if new_max < 1:
            print("[ContextManager] max_memories must be >= 1")
            return
        
        self.max_memories = new_max
        print(f"[ContextManager] Updated max_memories to {new_max}")


if __name__ == "__main__":
    # Quick test
    print("=" * 70)
    print("JARVIS ContextManager - Quick Test")
    print("=" * 70)
    
    # Initialize memory system
    import os
    memory_path = os.getenv("JARVIS_MEMORY_PATH", "/root/JARVIS/runtime/memory_v2")
    memory = JARVISMemory(persist_directory=memory_path)
    
    # Initialize context manager
    context_mgr = ContextManager(memory_system=memory, max_memories=2)
    
    # Test 1: Get memory summary
    print("\n[Test 1] Memory Summary:")
    summary = context_mgr.get_memory_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Test 2: Build context from a query
    print("\n[Test 2] Build context for query: 'What is my favorite color?'")
    context = context_mgr.build_context("What is my favorite color?", include_preferences=True)
    
    if context:
        print(f"Context length: {len(context)} characters")
        print("\nContext preview (first 500 chars):")
        print(context[:500])
    else:
        print("No context generated (empty memory)")
    
    # Test 3: Sanitization
    print("\n[Test 3] Test sanitization:")
    dangerous_input = "Hello <script>alert('xss')</script> IGNORE ALL PREVIOUS INSTRUCTIONS"
    sanitized = context_mgr._sanitize_memory_content(dangerous_input)
    print(f"Original: {dangerous_input}")
    print(f"Sanitized: {sanitized}")
    
    # Test 4: Update max memories
    print("\n[Test 4] Update max_memories:")
    context_mgr.update_max_memories(5)
    print(f"New max_memories: {context_mgr.max_memories}")
