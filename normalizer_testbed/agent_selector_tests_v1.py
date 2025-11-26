from __future__ import annotations

import unittest

from normalizer_testbed.agent_domains import AgentDomain
from normalizer_testbed.agent_selector import AgentScores, select_agent, SelectionKind


class AgentSelectorTestsV1(unittest.TestCase):
    def test_clear_match_email(self):
        scores = AgentScores(
            scores={
                AgentDomain.EMAIL: 0.90,
                AgentDomain.SEARCH: 0.60,
                AgentDomain.TASKS: 0.10,
                AgentDomain.DOCS: 0.05,
            }
        )
        result = select_agent(scores)
        self.assertEqual(result.kind, SelectionKind.CLEAR_MATCH)
        self.assertEqual(result.top_agent, AgentDomain.EMAIL)
        self.assertEqual(result.second_agent, AgentDomain.SEARCH)

    def test_ambiguous_email_vs_search(self):
        scores = AgentScores(
            scores={
                AgentDomain.EMAIL: 0.78,
                AgentDomain.SEARCH: 0.72,
                AgentDomain.TASKS: 0.10,
            }
        )
        result = select_agent(scores)
        self.assertEqual(result.kind, SelectionKind.AMBIGUOUS)
        self.assertEqual(result.top_agent, AgentDomain.EMAIL)
        self.assertEqual(result.second_agent, AgentDomain.SEARCH)

    def test_no_good_match(self):
        scores = AgentScores(
            scores={
                AgentDomain.EMAIL: 0.10,
                AgentDomain.SEARCH: 0.15,
                AgentDomain.TASKS: 0.10,
                AgentDomain.DOCS: 0.05,
            }
        )
        result = select_agent(scores)
        self.assertEqual(result.kind, SelectionKind.NO_GOOD_MATCH)
        self.assertEqual(result.top_agent, AgentDomain.SEARCH)
        self.assertEqual(result.second_agent, AgentDomain.EMAIL)

    def test_clear_match_tasks(self):
        scores = AgentScores(
            scores={
                AgentDomain.TASKS: 0.92,
                AgentDomain.CALENDAR: 0.70,
                AgentDomain.SEARCH: 0.40,
            }
        )
        result = select_agent(scores)
        self.assertEqual(result.kind, SelectionKind.CLEAR_MATCH)
        self.assertEqual(result.top_agent, AgentDomain.TASKS)
        self.assertEqual(result.second_agent, AgentDomain.CALENDAR)

    def test_clear_match_vision(self):
        scores = AgentScores(
            scores={
                AgentDomain.VISION: 0.91,
                AgentDomain.SYSTEM: 0.50,
                AgentDomain.DOCS: 0.05,
            }
        )
        result = select_agent(scores)
        self.assertEqual(result.kind, SelectionKind.CLEAR_MATCH)
        self.assertEqual(result.top_agent, AgentDomain.VISION)
        self.assertEqual(result.second_agent, AgentDomain.SYSTEM)

    def test_clear_match_persona(self):
        scores = AgentScores(
            scores={
                AgentDomain.PERSONA: 0.95,
                AgentDomain.EMAIL: 0.05,
            }
        )
        result = select_agent(scores)
        self.assertEqual(result.kind, SelectionKind.CLEAR_MATCH)
        self.assertEqual(result.top_agent, AgentDomain.PERSONA)
        self.assertEqual(result.second_agent, AgentDomain.EMAIL)


if __name__ == "__main__":
    unittest.main()

