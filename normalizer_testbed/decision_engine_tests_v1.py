from __future__ import annotations

import unittest

from normalizer_testbed.agent_domains import AgentDomain
from normalizer_testbed.agent_selector import AgentScores, SelectionKind
from normalizer_testbed.capability_registry import DecisionOutcome
from normalizer_testbed.decision_engine_v1 import ProposedIntent, decide_intent_outcome


class DecisionEngineTestsV1(unittest.TestCase):
    def test_ambiguous_calendar_vs_tasks(self):
        # Ambiguous case
        scores = AgentScores(
            scores={
                AgentDomain.CALENDAR: 0.78,
                AgentDomain.TASKS: 0.72,
                AgentDomain.SEARCH: 0.30,
            }
        )
        proposed = ProposedIntent(domain="calendar", action="create_event")
        outcome, selection = decide_intent_outcome(scores, proposed)
        self.assertEqual(selection.kind, SelectionKind.AMBIGUOUS)
        self.assertEqual(outcome, DecisionOutcome.CLARIFY)

    def test_clear_calendar_but_unknown_action(self):
        scores = AgentScores(
            scores={
                AgentDomain.CALENDAR: 0.90,
                AgentDomain.TASKS: 0.40,
            }
        )
        proposed = ProposedIntent(domain="calendar", action="create_booking")  # unsupported
        outcome, selection = decide_intent_outcome(scores, proposed)
        self.assertEqual(selection.kind, SelectionKind.CLEAR_MATCH)
        self.assertEqual(outcome, DecisionOutcome.CLARIFY)

    def test_clear_reminder_accept(self):
        scores = AgentScores(
            scores={
                AgentDomain.TASKS: 0.92,
                AgentDomain.CALENDAR: 0.70,
                AgentDomain.SEARCH: 0.40,
            }
        )
        proposed = ProposedIntent(domain="tasks", action="create_reminder")
        outcome, selection = decide_intent_outcome(scores, proposed)
        self.assertEqual(selection.kind, SelectionKind.CLEAR_MATCH)
        self.assertEqual(outcome, DecisionOutcome.ACCEPT)

    def test_persona_bork_accept(self):
        scores = AgentScores(
            scores={
                AgentDomain.PERSONA: 0.95,
                AgentDomain.EMAIL: 0.05,
            }
        )
        proposed = ProposedIntent(domain="persona", action="enable_bork_mode")
        outcome, selection = decide_intent_outcome(scores, proposed)
        self.assertEqual(selection.kind, SelectionKind.CLEAR_MATCH)
        self.assertEqual(outcome, DecisionOutcome.ACCEPT)

    def test_no_good_match_clarify(self):
        scores = AgentScores(
            scores={
                AgentDomain.EMAIL: 0.10,
                AgentDomain.SEARCH: 0.15,
                AgentDomain.TASKS: 0.10,
                AgentDomain.DOCS: 0.05,
            }
        )
        proposed = ProposedIntent(domain="search", action="search_web")
        outcome, selection = decide_intent_outcome(scores, proposed)
        self.assertEqual(selection.kind, SelectionKind.NO_GOOD_MATCH)
        self.assertEqual(outcome, DecisionOutcome.CLARIFY)


if __name__ == "__main__":
    unittest.main()

