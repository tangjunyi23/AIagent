import unittest

from audit_agents.state import create_initial_state
from audit_agents.supervisor import (
    build_supervisor_graph,
    request_dangerous_action_approval,
    triage_sample,
)


class SupervisorTests(unittest.TestCase):
    def test_triage_sample_adds_agent_event(self) -> None:
        state = create_initial_state(
            analysis_id="analysis_123",
            project_id="project_123",
            sample_ids=["sample_123"],
            scenario="firmware",
            thread_id="thread_123",
        )

        update = triage_sample(state)

        self.assertEqual(update["analysis"]["status"], "running")
        self.assertEqual(update["events"][0]["type"], "agent.started")

    def test_approval_placeholder_creates_request_without_running_tool(self) -> None:
        state = create_initial_state(
            analysis_id="analysis_123",
            project_id="project_123",
            sample_ids=["sample_123"],
            scenario="firmware",
            thread_id="thread_123",
        )

        update = request_dangerous_action_approval(state)

        self.assertEqual(update["analysis"]["status"], "interrupted")
        self.assertEqual(update["approval_requests"][0]["action"], "firmware-emulation")
        self.assertEqual(update["events"][0]["type"], "approval.requested")

    def test_approval_placeholder_reuses_existing_pending_request(self) -> None:
        state = create_initial_state(
            analysis_id="analysis_123",
            project_id="project_123",
            sample_ids=["sample_123"],
            scenario="firmware",
            thread_id="thread_123",
        )
        state["approval_requests"].append(
            {
                "id": "approval_analysis_123_firmware_emulation",
                "analysis_id": "analysis_123",
                "project_id": "project_123",
                "interrupt_id": "interrupt_analysis_123_firmware_emulation",
                "action": "firmware-emulation",
                "status": "pending",
                "requested_by_agent": "supervisor",
                "reason": "Firmware emulation is a dangerous dynamic action.",
                "risk_summary": "Execution is blocked until a human approves sandbox limits.",
                "proposed_parameters": {},
                "created_at": "",
                "decided_at": None,
                "decided_by": None,
                "decision_reason": None,
            }
        )

        update = request_dangerous_action_approval(state)

        self.assertEqual(update["analysis"]["status"], "interrupted")
        self.assertEqual(len(update["approval_requests"]), 1)
        self.assertEqual(update["events"], [])

    def test_build_supervisor_graph_compiles(self) -> None:
        graph = build_supervisor_graph()

        self.assertIsNotNone(graph)
        self.assertEqual(graph.nodes, ("triage", "approval_gate"))


if __name__ == "__main__":
    unittest.main()
