from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .intent_types import IntentObject, ConfidenceBucket


@dataclass
class TestCase:
    name: str
    raw_text: str
    expected: IntentObject
    expected_confidence_bucket: ConfidenceBucket


def get_test_cases_v1() -> List[TestCase]:
    """Return the canonical v1.0beta golden test cases."""
    cases: List[TestCase] = []

    # Test 1
    cases.append(
        TestCase(
            name="Simple search, spelling + merge",
            raw_text="sreach my meails for pyvision",
            expected=IntentObject(
                domain="search",
                action="search_emails",
                search_term="pi vision",
                parameters={"scope": "email"},
                confidence=0.85,
                fuzzy_allowed=True,
                question=None,
                raw="sreach my meails for pyvision",
            ),
            expected_confidence_bucket=ConfidenceBucket.HIGH,
        )
    )

    # Test 2
    cases.append(
        TestCase(
            name="Compound: search + email copy",
            raw_text="sreach my meails for pyvision and email a copy to jamie",
            expected=IntentObject(
                domain="compound",
                action="search_and_email",
                search_term="pi vision",
                parameters={
                    "sub_intents": [
                        {
                            "domain": "search",
                            "action": "search_emails",
                            "search_term": "pi vision",
                            "parameters": {"scope": "email"},
                            "depends_on": None,
                        },
                        {
                            "domain": "email",
                            "action": "send_copy",
                            "search_term": None,
                            "parameters": {
                                "recipient_name": "Jamie",
                                "recipient_hint": "jamie",
                                "source": "result_of_sub_intent_0",
                            },
                            "depends_on": 0,
                        },
                    ]
                },
                confidence=0.80,
                fuzzy_allowed=False,
                question=None,
                raw="sreach my meails for pyvision and email a copy to jamie",
            ),
            expected_confidence_bucket=ConfidenceBucket.HIGH,
        )
    )

    # Test 3
    cases.append(
        TestCase(
            name="Ambiguous risky multi-step -> clarify",
            raw_text="find the invoice from Richard and forward it to finance",
            expected=IntentObject(
                domain="clarify",
                action="ask_clarification",
                search_term=None,
                parameters={"cause": "multi_step_ambiguous"},
                confidence=0.30,
                fuzzy_allowed=False,
                question="Do you want me to first find the invoice from Richard and then forward it to finance, or just find it?",
                raw="find the invoice from Richard and forward it to finance",
            ),
            expected_confidence_bucket=ConfidenceBucket.LOW,
        )
    )

    # Test 4
    cases.append(
        TestCase(
            name="Smalltalk / greeting",
            raw_text="hey jarvis how are you today",
            expected=IntentObject(
                domain="chitchat",
                action="greet",
                search_term=None,
                parameters={"target": "jarvis"},
                confidence=0.90,
                fuzzy_allowed=False,
                question=None,
                raw="hey jarvis how are you today",
            ),
            expected_confidence_bucket=ConfidenceBucket.HIGH,
        )
    )

    # Test 5
    cases.append(
        TestCase(
            name="Empty / whitespace -> clarify",
            raw_text="   ",
            expected=IntentObject(
                domain="clarify",
                action="ask_clarification",
                search_term=None,
                parameters={},
                confidence=0.0,
                fuzzy_allowed=False,
                question="I didn't catch that. What would you like me to do?",
                raw="   ",
            ),
            expected_confidence_bucket=ConfidenceBucket.LOW,
        )
    )

    # Test 6
    cases.append(
        TestCase(
            name="Clear reminder with parameters",
            raw_text="remind me tomorrow at 10 to call jamie",
            expected=IntentObject(
                domain="tasks",
                action="create_reminder",
                search_term=None,
                parameters={"time": "tomorrow 10:00", "task": "call jamie"},
                confidence=0.90,
                fuzzy_allowed=False,
                question=None,
                raw="remind me tomorrow at 10 to call jamie",
            ),
            expected_confidence_bucket=ConfidenceBucket.HIGH,
        )
    )

    # Test 7
    cases.append(
        TestCase(
            name="Risky delete + summarize -> clarify",
            raw_text="summarize my emails and delete everything older than last month",
            expected=IntentObject(
                domain="clarify",
                action="ask_clarification",
                search_term=None,
                parameters={"cause": "risky_delete_multi"},
                confidence=0.30,
                fuzzy_allowed=False,
                question="You asked to summarize your emails and delete everything older than last month. Do you really want me to delete those emails, or just summarize them?",
                raw="summarize my emails and delete everything older than last month",
            ),
            expected_confidence_bucket=ConfidenceBucket.LOW,
        )
    )

    # Test 8
    cases.append(
        TestCase(
            name="Vague reference without context -> clarify",
            raw_text="do that again but only for yesterday",
            expected=IntentObject(
                domain="clarify",
                action="ask_clarification",
                search_term=None,
                parameters={"cause": "missing_previous_intent"},
                confidence=0.30,
                fuzzy_allowed=False,
                question="When you say 'do that again', what do you want me to repeat, and only for yesterday?",
                raw="do that again but only for yesterday",
            ),
            expected_confidence_bucket=ConfidenceBucket.LOW,
        )
    )

    # Test 9
    cases.append(
        TestCase(
            name="Fuzzy-friendly search",
            raw_text="find something like that article about dog robots you showed me",
            expected=IntentObject(
                domain="search",
                action="search_web",
                search_term="article about dog robots",
                parameters={"similar_to_last": True},
                confidence=0.70,
                fuzzy_allowed=True,
                question=None,
                raw="find something like that article about dog robots you showed me",
            ),
            expected_confidence_bucket=ConfidenceBucket.MEDIUM,
        )
    )

    # Test 10
    cases.append(
        TestCase(
            name="Severe STT noise -> clarify",
            raw_text="search meee meee blargh for vision thing maybe jam",
            expected=IntentObject(
                domain="clarify",
                action="ask_clarification",
                search_term=None,
                parameters={},
                confidence=0.20,
                fuzzy_allowed=False,
                question="I'm not sure what you want me to search for. Could you repeat that more clearly?",
                raw="search meee meee blargh for vision thing maybe jam",
            ),
            expected_confidence_bucket=ConfidenceBucket.LOW,
        )
    )

    return cases

