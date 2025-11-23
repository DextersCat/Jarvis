"""
ProactiveSuggestionEngine - Intelligent Suggestion System
Analyzes context and provides proactive suggestions

Created: November 15, 2025
Phase: 2 - Enhanced Intelligence & JARVIS Personality
Week: 2 - Personality Framework & Proactive Logic
"""

import re
from typing import List, Dict, Optional
from datetime import datetime, time


class ProactiveSuggestionEngine:
    """
    Generates proactive suggestions based on context and rules
    Implements JARVIS butler-like anticipatory behavior
    """
    
    def __init__(self):
        """
        Initialize ProactiveSuggestionEngine with rule patterns
        """
        # System health monitoring keywords
        self.health_keywords = [
            "error", "crash", "failure", "bug", "issue", "problem",
            "broken", "not working", "failed", "exception", "warning"
        ]
        
        # Stress indicators
        self.stress_keywords = [
            "stressed", "overwhelmed", "busy", "tired", "exhausted",
            "frustrated", "deadline", "urgent", "rush", "pressure"
        ]
        
        # Project state keywords
        self.project_keywords = [
            "project", "task", "implementation", "development", "build",
            "deploy", "test", "debug", "feature", "fix", "update"
        ]
        
        print("[ProactiveSuggestionEngine] Initialized with 3 rule patterns")
    
    def analyze_and_suggest(
        self,
        user_input: str,
        conversation_history: Optional[List[str]] = None,
        current_time: Optional[datetime] = None
    ) -> Optional[str]:
        """
        Analyze user input and generate proactive suggestions
        
        Args:
            user_input: Current user message
            conversation_history: Recent conversation history (optional)
            current_time: Current datetime (optional, defaults to now)
            
        Returns:
            str: Proactive suggestion or None if no suggestion warranted
        """
        if not user_input:
            return None
        
        if current_time is None:
            current_time = datetime.now()
        
        # Convert to lowercase for analysis
        input_lower = user_input.lower()
        
        # Rule 1: System Health Monitoring
        health_suggestion = self._check_system_health(input_lower)
        if health_suggestion:
            return health_suggestion
        
        # Rule 2: Stress Minimization
        stress_suggestion = self._check_stress_indicators(input_lower, current_time)
        if stress_suggestion:
            return stress_suggestion
        
        # Rule 3: Project State Awareness
        project_suggestion = self._check_project_state(input_lower, conversation_history)
        if project_suggestion:
            return project_suggestion
        
        # No proactive suggestion needed
        return None
    
    def _check_system_health(self, input_lower: str) -> Optional[str]:
        """
        Rule 1: Monitor for system health issues
        
        Args:
            input_lower: Lowercase user input
            
        Returns:
            str: Health-related suggestion or None
        """
        # Check for health keywords
        detected_issues = [kw for kw in self.health_keywords if kw in input_lower]
        
        if len(detected_issues) == 0:
            return None
        
        # Multiple issues detected - suggest systematic troubleshooting
        if len(detected_issues) >= 2:
            return (
                "I notice multiple system issues mentioned, Sir. May I suggest a systematic "
                "diagnostic approach? We could review logs, verify configurations, and "
                "isolate the root cause methodically."
            )
        
        # Single issue - offer specific assistance
        issue = detected_issues[0]
        
        if issue in ["error", "exception"]:
            return (
                "I observe an error has occurred, Sir. Shall I assist with examining "
                "the stack trace and error logs to identify the root cause?"
            )
        
        elif issue in ["crash", "failure", "broken", "not working"]:
            return (
                "A system failure is most concerning, Sir. Would you like me to help "
                "verify the environment configuration and dependencies?"
            )
        
        elif issue == "warning":
            return (
                "Warnings detected, Sir. Whilst not critical, addressing them now may "
                "prevent future complications. Shall we investigate?"
            )
        
        # Generic health suggestion
        return (
            "I detect a technical concern, Sir. How may I assist in resolving this matter?"
        )
    
    def _check_stress_indicators(self, input_lower: str, current_time: datetime) -> Optional[str]:
        """
        Rule 2: Detect stress and suggest breaks or prioritization
        
        Args:
            input_lower: Lowercase user input
            current_time: Current datetime
            
        Returns:
            str: Stress-related suggestion or None
        """
        # Check for stress keywords
        detected_stress = [kw for kw in self.stress_keywords if kw in input_lower]
        
        if len(detected_stress) == 0:
            return None
        
        # Time-based suggestions
        current_hour = current_time.hour
        
        # Late night work (10 PM - 5 AM)
        if current_hour >= 22 or current_hour <= 5:
            return (
                "Sir, it is rather late. Whilst I admire your dedication, rest is essential "
                "for optimal performance. Might I suggest resuming tomorrow with renewed focus?"
            )
        
        # Early morning (5 AM - 8 AM)
        elif current_hour >= 5 and current_hour < 8:
            return (
                "Good morning, Sir. I note the early hour. Shall I prepare a summary of "
                "today's priorities whilst you attend to breakfast?"
            )
        
        # Long work sessions - suggest break
        if any(kw in input_lower for kw in ["tired", "exhausted", "overwhelmed"]):
            return (
                "Sir, may I respectfully suggest a brief respite? A short walk or tea break "
                "often provides clarity and renewed energy for tackling complex challenges."
            )
        
        # Deadline pressure - suggest prioritization
        if any(kw in input_lower for kw in ["deadline", "urgent", "rush"]):
            return (
                "I understand the urgency, Sir. Shall we prioritize the most critical tasks "
                "first? A systematic approach often proves more efficient under time pressure."
            )
        
        # Generic stress response
        return (
            "I sense some pressure, Sir. How might I assist in easing your burden? "
            "Perhaps task prioritization or automated assistance?"
        )
    
    def _check_project_state(
        self,
        input_lower: str,
        conversation_history: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Rule 3: Awareness of project state and context
        
        Args:
            input_lower: Lowercase user input
            current_conversation: Recent conversation context
            
        Returns:
            str: Project-related suggestion or None
        """
        # Check for project keywords
        detected_project = [kw for kw in self.project_keywords if kw in input_lower]
        
        if len(detected_project) == 0:
            return None
        
        # Analyze project phase from keywords
        
        # Starting new work
        if "start" in input_lower or "begin" in input_lower or "create" in input_lower:
            return (
                "Commencing new work, Sir? Shall I prepare the development environment "
                "and review any relevant documentation or previous implementations?"
            )
        
        # Testing phase
        if "test" in input_lower:
            return (
                "Testing is prudent, Sir. Would you like me to review test coverage, "
                "prepare test data, or verify edge cases?"
            )
        
        # Deployment/production
        if "deploy" in input_lower or "production" in input_lower or "release" in input_lower:
            return (
                "Deployment is a critical phase, Sir. Shall I verify the checklist: "
                "tests passing, documentation updated, backups confirmed, and rollback plan prepared?"
            )
        
        # Debugging
        if "debug" in input_lower or "fix" in input_lower:
            return (
                "Debugging requires systematic analysis, Sir. May I assist by reviewing "
                "logs, checking recent changes, or isolating the affected components?"
            )
        
        # General project work - check if JARVIS project mentioned
        if "jarvis" in input_lower:
            return (
                "Ah, the ULTIMATE JARVIS project, Sir. I am, of course, most invested in my "
                "own development. How may I assist in advancing my capabilities?"
            )
        
        # Generic project suggestion
        return None  # Don't be too chatty for generic project mentions
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get statistics about suggestion patterns
        
        Returns:
            dict: Statistics about the engine
        """
        return {
            "health_patterns": len(self.health_keywords),
            "stress_patterns": len(self.stress_keywords),
            "project_patterns": len(self.project_keywords),
            "total_rules": 3
        }


if __name__ == "__main__":
    # Quick test
    print("=" * 70)
    print("JARVIS ProactiveSuggestionEngine - Quick Test")
    print("=" * 70)
    
    engine = ProactiveSuggestionEngine()
    
    # Test 1: System health detection
    print("\n[Test 1] System Health:")
    test_inputs = [
        "I'm getting an error in the code",
        "The system crashed again",
        "There's a warning in the logs"
    ]
    for inp in test_inputs:
        suggestion = engine.analyze_and_suggest(inp)
        print(f"  Input: '{inp}'")
        print(f"  Suggestion: {suggestion}\n")
    
    # Test 2: Stress detection
    print("\n[Test 2] Stress Detection:")
    late_night = datetime(2025, 11, 15, 23, 30)  # 11:30 PM
    suggestion = engine.analyze_and_suggest(
        "I'm so tired but need to finish this",
        current_time=late_night
    )
    print(f"  Input: 'I'm so tired but need to finish this' (11:30 PM)")
    print(f"  Suggestion: {suggestion}\n")
    
    # Test 3: Project state
    print("\n[Test 3] Project State:")
    test_inputs = [
        "Let's start building the new feature",
        "Time to test this implementation",
        "Ready to deploy to production",
        "Working on the JARVIS project"
    ]
    for inp in test_inputs:
        suggestion = engine.analyze_and_suggest(inp)
        print(f"  Input: '{inp}'")
        print(f"  Suggestion: {suggestion}\n")
    
    # Test 4: No suggestion needed
    print("\n[Test 4] No Suggestion:")
    suggestion = engine.analyze_and_suggest("What's the weather like?")
    print(f"  Input: 'What's the weather like?'")
    print(f"  Suggestion: {suggestion}")
    
    # Stats
    print(f"\n[Stats] {engine.get_statistics()}")
