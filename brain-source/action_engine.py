"""
Action Engine - Orchestration & Tool Planning
Decides which tools to use and coordinates the query pipeline
Phase E - Orchestration & Action Engine
"""
import logging
import json
import os
from typing import Dict, List, Tuple, Optional, Any

from openai import OpenAI

from core.email_service import EmailService
from core.calendar_service import CalendarService
from core.prompt_engine import PromptEngine

logger = logging.getLogger(__name__)


class ActionEngine:
    """
    Action Engine for JARVIS - decides which tools to use and orchestrates
    the complete query pipeline
    
    Single-pass orchestration:
    1. Plan tools (using LLM)
    2. Run tools (email/calendar services)
    3. Build prompt (PromptEngine)
    4. Get final answer (LLM)
    """
    
    def __init__(
        self,
        openai_client: OpenAI,
        memory_provider: Any,
        system_prompt_provider: Any,
        email_service: Optional[EmailService] = None,
        calendar_service: Optional[CalendarService] = None
    ):
        """
        Initialize Action Engine
        
        Args:
            openai_client: OpenAI client for LLM calls
            memory_provider: Object with recall(query) method
            system_prompt_provider: Object with get_system_prompt() method
            email_service: EmailService instance (optional)
            calendar_service: CalendarService instance (optional)
        """
        self.openai_client = openai_client
        self.memory_provider = memory_provider
        self.system_prompt_provider = system_prompt_provider
        
        # Initialize services lazily to avoid OAuth prompts on startup
        self._email_service = email_service
        self._calendar_service = calendar_service
        
        # Initialize PromptEngine
        self.prompt_engine = PromptEngine(
            system_prompt_provider=system_prompt_provider,
            memory_provider=memory_provider,
            max_tokens=8000,
            output_reserve=4000
        )
        
        logger.info("Action Engine initialized")
    
    @property
    def email_service(self) -> Optional[EmailService]:
        """Lazy-load email service"""
        if self._email_service is None:
            try:
                self._email_service = EmailService()
                logger.info("Email service initialized")
            except Exception as e:
                logger.warning(f"Email service unavailable: {e}")
        return self._email_service
    
    @property
    def calendar_service(self) -> Optional[CalendarService]:
        """Lazy-load calendar service"""
        if self._calendar_service is None:
            try:
                self._calendar_service = CalendarService()
                logger.info("Calendar service initialized")
            except Exception as e:
                logger.warning(f"Calendar service unavailable: {e}")
        return self._calendar_service
    
    def plan_tools(
        self,
        query: str,
        memory_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Use LLM to decide which tools to use
        
        Args:
            query: User's query
            memory_context: Optional memory context string
        
        Returns:
            Tool plan dict with:
            - use_email (bool)
            - use_calendar (bool)
            - email_time_window (str or None)
            - calendar_horizon (str or None)
            - reason (str)
        """
        logger.info(f"Planning tools for query: {query}")
        
        # System prompt for tool planning
        system_prompt = """You are a tool planner for JARVIS assistant. 
You must respond ONLY with a JSON object. No other text before or after.

Your job is to decide which tools to use based on the user's query:
- use_email: true if query relates to emails, messages, or inbox
- use_calendar: true if query relates to schedule, events, meetings, or time
- email_time_window: time window like "3 hours", "24 hours", "1 hour", or null
- calendar_horizon: horizon like "today", "24 hours", "7 days", or null
- reason: brief explanation (1 sentence)

Examples:
{
  "use_email": false,
  "use_calendar": true,
  "email_time_window": null,
  "calendar_horizon": "24 hours",
  "reason": "Query asks about calendar/schedule"
}

{
  "use_email": true,
  "use_calendar": false,
  "email_time_window": "3 hours",
  "calendar_horizon": null,
  "reason": "Query asks about recent emails"
}

{
  "use_email": true,
  "use_calendar": true,
  "email_time_window": "24 hours",
  "calendar_horizon": "24 hours",
  "reason": "Query asks for daily overview"
}

{
  "use_email": false,
  "use_calendar": false,
  "email_time_window": null,
  "calendar_horizon": null,
  "reason": "Query is general knowledge, no tools needed"
}

Respond ONLY with valid JSON. No markdown, no code blocks."""
        
        # Build user message
        user_message = f"Query: {query}"
        if memory_context:
            user_message += f"\n\nMemory context: {memory_context}"
        
        try:
            # Call LLM in JSON mode
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            
            # Parse JSON response
            tool_plan_str = response.choices[0].message.content
            tool_plan = json.loads(tool_plan_str)
            
            # Validate required fields
            required_fields = [
                'use_email', 'use_calendar',
                'email_time_window', 'calendar_horizon', 'reason'
            ]
            for field in required_fields:
                if field not in tool_plan:
                    logger.warning(
                        f"Missing field '{field}' in tool plan, using fallback"
                    )
                    return self._fallback_tool_plan(query)
            
            logger.info(f"Tool plan: {tool_plan}")
            return tool_plan
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse tool plan JSON: {e}")
            return self._fallback_tool_plan(query)
        except Exception as e:
            logger.error(f"Tool planning failed: {e}")
            return self._fallback_tool_plan(query)
    
    def _fallback_tool_plan(self, query: str) -> Dict[str, Any]:
        """
        Simple rule-based fallback if LLM planning fails
        
        Args:
            query: User's query
        
        Returns:
            Basic tool plan based on keyword matching
        """
        query_lower = query.lower()
        
        # Simple keyword matching
        use_email = any(
            kw in query_lower
            for kw in ['email', 'mail', 'inbox', 'message', 'unread']
        )
        use_calendar = any(
            kw in query_lower
            for kw in [
                'calendar', 'schedule', 'meeting', 'event',
                'appointment', 'today', 'tomorrow', 'afternoon'
            ]
        )
        
        # Default time windows
        email_time_window = "24 hours" if use_email else None
        calendar_horizon = "24 hours" if use_calendar else None
        
        fallback_plan = {
            "use_email": use_email,
            "use_calendar": use_calendar,
            "email_time_window": email_time_window,
            "calendar_horizon": calendar_horizon,
            "reason": "Fallback rule-based planning (LLM planning failed)"
        }
        
        logger.info(f"Using fallback tool plan: {fallback_plan}")
        return fallback_plan
    
    def run_tools(
        self,
        tool_plan: Dict[str, Any]
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Execute tools based on the plan
        
        Args:
            tool_plan: Tool plan dict from plan_tools()
        
        Returns:
            Tuple of (email_data, calendar_data)
            Each is a list of dicts (may be empty)
        """
        email_data = []
        calendar_data = []
        
        # Run email tool if requested
        if tool_plan.get('use_email') and tool_plan.get('email_time_window'):
            try:
                if self.email_service:
                    time_window = tool_plan['email_time_window']
                    logger.info(f"Fetching emails from last {time_window}")
                    email_data = self.email_service.get_unread_emails_since(
                        time_ago=time_window,
                        max_results=20
                    )
                    logger.info(f"Retrieved {len(email_data)} emails")
                else:
                    logger.warning("Email service not available")
            except Exception as e:
                logger.error(f"Email tool failed: {e}")
                # Don't crash, just return empty
        
        # Run calendar tool if requested
        if tool_plan.get('use_calendar') and tool_plan.get('calendar_horizon'):
            try:
                if self.calendar_service:
                    # For now, always use Europe/London and 24 hours
                    # Can expand to parse calendar_horizon later
                    logger.info("Fetching calendar events for next 24 hours")
                    calendar_data = self.calendar_service.get_events_for_next_24_hours(
                        timezone_str="Europe/London"
                    )
                    logger.info(f"Retrieved {len(calendar_data)} events")
                else:
                    logger.warning("Calendar service not available")
            except Exception as e:
                logger.error(f"Calendar tool failed: {e}")
                # Don't crash, just return empty
        
        return email_data, calendar_data
    
    def orchestrate_query(self, user_query: str) -> Dict[str, Any]:
        """
        Main orchestration pipeline
        
        Single-pass flow:
        1. Retrieve memory
        2. Plan tools
        3. Run tools
        4. Build prompt
        5. Get LLM answer
        6. Return structured response
        
        Args:
            user_query: User's natural language query
        
        Returns:
            Response dict with:
            - assistant_message (str): Final answer
            - tool_plan (dict): Tool planning decision
            - actions_taken (list): Log of tools executed
        """
        logger.info(f"Orchestrating query: {user_query}")
        
        # Step 1: Retrieve memory
        memory_context = ""
        try:
            if self.memory_provider:
                memory_results = self.memory_provider.recall(user_query)
                if memory_results:
                    # Format memory results
                    if isinstance(memory_results, str):
                        memory_context = memory_results
                    elif isinstance(memory_results, list):
                        memory_context = "\n".join(
                            f"- {mem}" for mem in memory_results
                        )
                logger.info(f"Retrieved memory context: {len(memory_context)} chars")
        except Exception as e:
            logger.error(f"Memory retrieval failed: {e}")
        
        # Step 2: Plan tools
        tool_plan = self.plan_tools(user_query, memory_context)
        
        # Step 3: Run tools
        email_data, calendar_data = self.run_tools(tool_plan)
        
        # Track actions taken
        actions_taken = []
        
        if tool_plan.get('use_email'):
            actions_taken.append({
                "tool": "email_service.get_unread_emails_since",
                "params": {"time_ago": tool_plan.get('email_time_window')},
                "items_returned": len(email_data)
            })
        
        if tool_plan.get('use_calendar'):
            actions_taken.append({
                "tool": "calendar_service.get_events_for_next_24_hours",
                "params": {"timezone": "Europe/London"},
                "items_returned": len(calendar_data)
            })
        
        # Step 4: Build final prompt
        final_prompt = self.prompt_engine.build_final_prompt(
            query=user_query,
            email_data=email_data,
            calendar_data=calendar_data,
            memory_context=memory_context,  # Pass pre-fetched memory
            max_tokens=8000
        )
        
        logger.info(f"Built final prompt: {len(final_prompt)} chars")
        
        # Step 5: Get LLM final answer
        assistant_message = ""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": final_prompt}],
                temperature=0.7
            )
            assistant_message = response.choices[0].message.content
            logger.info(f"Generated response: {len(assistant_message)} chars")
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            assistant_message = (
                "I apologize, but I encountered an error generating a response. "
                "Please try again."
            )
        
        # Step 6: Return structured response
        return {
            "assistant_message": assistant_message,
            "tool_plan": tool_plan,
            "actions_taken": actions_taken
        }
