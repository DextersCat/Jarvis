"""
Prompt Engine - Context Assembly and Token Management
Builds optimized prompts for LLM with proper section delineation
"""
import logging
from typing import List, Dict, Optional, Any

from core.config import MAX_PROMPT_TOKENS, MODEL_OUTPUT_RESERVE

logger = logging.getLogger(__name__)


class PromptEngine:
    """
    Assembles final prompts with memory, calendar, and email context
    Handles token budget management and intelligent pruning
    """
    
    def __init__(
        self,
        system_prompt_provider: Any,
        memory_provider: Any,
        max_tokens: int = MAX_PROMPT_TOKENS,
        output_reserve: int = MODEL_OUTPUT_RESERVE
    ):
        """
        Initialize Prompt Engine
        
        Args:
            system_prompt_provider: Object with get_system_prompt() method
            memory_provider: Object with recall(query) method
            max_tokens: Maximum tokens for assembled prompt
            output_reserve: Tokens to reserve for model output
        """
        self.system_prompt_provider = system_prompt_provider
        self.memory_provider = memory_provider
        self.max_tokens = max_tokens
        self.output_reserve = output_reserve
        self.available_tokens = max_tokens - output_reserve
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Rough token estimation (4 chars Ôëê 1 token)
        
        Args:
            text: String to estimate
        
        Returns:
            Approximate token count
        """
        return len(text) // 4
    
    def _truncate_to_budget(
        self,
        sections: Dict[str, str],
        budget: int
    ) -> Dict[str, str]:
        """
        Intelligently prune sections to fit token budget
        
        Priority:
        1. SYSTEM_INSTRUCTIONS (always kept)
        2. USER_QUERY (always kept)
        3. MEMORY (pruned oldest first)
        4. CALENDAR (pruned least important)
        5. EMAILS (pruned oldest first)
        
        Args:
            sections: Dict of section names to content
            budget: Target token count
        
        Returns:
            Pruned sections dict
        """
        # Calculate current usage
        current_tokens = sum(
            self._estimate_tokens(content) 
            for content in sections.values()
        )
        
        if current_tokens <= budget:
            logger.info(
                f"Prompt within budget: {current_tokens}/{budget} tokens"
            )
            return sections
        
        logger.warning(
            f"Prompt over budget: {current_tokens}/{budget} tokens. "
            f"Pruning..."
        )
        
        # Never prune these
        protected = ['SYSTEM_INSTRUCTIONS', 'USER_QUERY']
        protected_tokens = sum(
            self._estimate_tokens(sections.get(k, ''))
            for k in protected
        )
        
        remaining_budget = budget - protected_tokens
        
        # Prune in order: MEMORY ÔåÆ EMAILS ÔåÆ CALENDAR
        prunable = ['MEMORY', 'EMAILS', 'CALENDAR']
        
        for section_name in prunable:
            if remaining_budget >= current_tokens - protected_tokens:
                break
            
            content = sections.get(section_name, '')
            if not content:
                continue
            
            # Simple truncation: cut in half repeatedly
            while self._estimate_tokens(content) > remaining_budget // 3:
                lines = content.split('\n')
                if len(lines) <= 1:
                    break
                # Keep first half
                content = '\n'.join(lines[:len(lines)//2]) + '\n...(truncated)'
            
            sections[section_name] = content
            logger.info(f"Pruned {section_name} to fit budget")
        
        final_tokens = sum(
            self._estimate_tokens(content)
            for content in sections.values()
        )
        logger.info(f"Pruned prompt: {final_tokens}/{budget} tokens")
        
        return sections
    
    def build_final_prompt(
        self,
        query: str,
        email_data: List[Dict],
        calendar_data: List[Dict],
        memory_context: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Build final prompt with all context sections
        
        Section order:
        1. SYSTEM_INSTRUCTIONS
        2. USER_QUERY
        3. MEMORY
        4. CALENDAR
        5. EMAILS
        
        Args:
            query: User's query string
            email_data: List of email dicts from email_service
            calendar_data: List of event dicts from calendar_service
            memory_context: Pre-retrieved memory context string (optional)
            max_tokens: Override default max_tokens
        
        Returns:
            Assembled prompt string with XML section tags
        """
        budget = max_tokens or self.available_tokens
        
        # Gather sections
        sections = {}
        
        # 1. System instructions
        try:
            system_prompt = self.system_prompt_provider.get_system_prompt()
            sections['SYSTEM_INSTRUCTIONS'] = system_prompt
        except Exception as e:
            logger.error(f"Failed to get system prompt: {e}")
            sections['SYSTEM_INSTRUCTIONS'] = (
                "You are JARVIS, a helpful AI assistant."
            )
        
        # 2. User query
        sections['USER_QUERY'] = query
        
        # 3. Memory - use provided context
        sections['MEMORY'] = memory_context or ""
        
        # 4. Calendar
        if calendar_data:
            calendar_text = "\n".join(
                f"- {event['start_time']} to {event['end_time']}: "
                f"{event['summary']}"
                + (f" at {event['location']}" if event.get('location') else "")
                for event in calendar_data
            )
            sections['CALENDAR'] = calendar_text
        else:
            sections['CALENDAR'] = ""
        
        # 5. Emails
        if email_data:
            email_text = "\n\n".join(
                f"From: {email['sender']}\n"
                f"Subject: {email['subject']}\n"
                f"Preview: {email['snippet']}"
                + (" [PRIORITY]" if email.get('priority') else "")
                for email in email_data
            )
            sections['EMAILS'] = email_text
        else:
            sections['EMAILS'] = ""
        
        # Apply token budget
        sections = self._truncate_to_budget(sections, budget)
        
        # Assemble with XML tags
        prompt = (
            f"<SYSTEM_INSTRUCTIONS>\n{sections['SYSTEM_INSTRUCTIONS']}\n"
            f"</SYSTEM_INSTRUCTIONS>\n\n"
            f"<USER_QUERY>\n{sections['USER_QUERY']}\n</USER_QUERY>\n\n"
            f"<MEMORY>\n{sections['MEMORY']}\n</MEMORY>\n\n"
            f"<CALENDAR>\n{sections['CALENDAR']}\n</CALENDAR>\n\n"
            f"<EMAILS>\n{sections['EMAILS']}\n</EMAILS>"
        )
        
        final_tokens = self._estimate_tokens(prompt)
        logger.info(
            f"Final prompt assembled: {final_tokens} tokens "
            f"(budget: {budget})"
        )
        
        return prompt
