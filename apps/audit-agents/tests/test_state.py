import unittest

from audit_agents.state import create_initial_state


class StateTests(unittest.TestCase):
    def test_create_initial_state_uses_audit_common_contract_names(self) -> None:
        state = create_initial_state(
            analysis_id="analysis_123",
            project_id="project_123",
            sample_ids=["sample_123"],
            scenario="firmware",
            thread_id="thread_123",
        )

        self.assertEqual(state["analysis"]["status"], "queued")
        self.assertEqual(state["analysis"]["sample_ids"], ["sample_123"])
        self.assertEqual(state["events"], [])
        self.assertEqual(state["approval_requests"], [])


if __name__ == "__main__":
    unittest.main()
