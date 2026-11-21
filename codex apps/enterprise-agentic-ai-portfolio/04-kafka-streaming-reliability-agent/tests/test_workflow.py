import tempfile
import unittest
from pathlib import Path

from app.database import Repository
from app.models import ApprovalRequest
from app.simulator import SCENARIOS, SyntheticKafkaAdapter
from app.workflow import ReliabilityWorkflow, WorkflowConflict


class WorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        repository = Repository(Path(self.temp_dir.name) / "test.db")
        repository.initialize()
        self.repository = repository
        self.workflow = ReliabilityWorkflow(repository)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_approval_is_required_before_execution(self) -> None:
        incident = self.workflow.investigate("malformed_message")
        with self.assertRaises(WorkflowConflict):
            self.workflow.execute_and_validate(incident["incident_id"])

    def test_all_scenarios_validate_after_approved_remediation(self) -> None:
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario):
                incident = self.workflow.investigate(scenario)
                incident_id = incident["incident_id"]
                self.workflow.approve(incident_id, ApprovalRequest(
                    approved=True, approved_by="test-operator", reason="automated acceptance test"
                ))
                final = self.workflow.execute_and_validate(incident_id)
                self.assertEqual("VALIDATED", final["status"])
                self.assertTrue(final["validation"]["result"]["passed"])

        evaluation = self.repository.evaluation_summary()
        self.assertEqual(len(SCENARIOS), evaluation["correct"])
        self.assertEqual(1.0, evaluation["rca_accuracy"])

    def test_rejected_action_cannot_execute(self) -> None:
        incident = self.workflow.investigate("broker_outage")
        incident_id = incident["incident_id"]
        self.workflow.approve(incident_id, ApprovalRequest(
            approved=False, approved_by="test-operator", reason="blast radius is too large"
        ))
        with self.assertRaises(WorkflowConflict):
            self.workflow.execute_and_validate(incident_id)

    def test_unrelated_allow_listed_action_cannot_produce_healthy_validation(self) -> None:
        incident = self.workflow.investigate("malformed_message")
        incident_id = incident["incident_id"]
        self.workflow.approve(incident_id, ApprovalRequest(
            approved=True, approved_by="test-operator", reason="automated negative test"
        ))
        with self.repository.connect() as connection:
            row = connection.execute(
                "SELECT rca_json FROM incidents WHERE incident_id = ?", (incident_id,)
            ).fetchone()
            import json
            rca = json.loads(row["rca_json"])
            rca["recommended_actions"][0]["action_type"] = "restart_broker"
            connection.execute(
                "UPDATE incidents SET rca_json = ? WHERE incident_id = ?", (json.dumps(rca), incident_id)
            )

        result = self.workflow.execute_and_validate(incident_id)
        self.assertEqual("EXECUTION_FAILED", result["status"])
        self.assertFalse(result["execution"]["result"]["success"])
        self.assertIsNone(result["validation"])

    def test_wrong_action_parameters_cannot_produce_healthy_validation(self) -> None:
        incident = self.workflow.investigate("consumer_slowdown")
        incident_id = incident["incident_id"]
        self.workflow.approve(incident_id, ApprovalRequest(
            approved=True, approved_by="test-operator", reason="automated parameter integrity test"
        ))
        with self.repository.connect() as connection:
            row = connection.execute(
                "SELECT rca_json FROM incidents WHERE incident_id = ?", (incident_id,)
            ).fetchone()
            import json
            rca = json.loads(row["rca_json"])
            rca["recommended_actions"][0]["parameters"]["replicas"] = 99
            connection.execute(
                "UPDATE incidents SET rca_json = ? WHERE incident_id = ?", (json.dumps(rca), incident_id)
            )

        result = self.workflow.execute_and_validate(incident_id)
        self.assertEqual("EXECUTION_FAILED", result["status"])
        self.assertFalse(result["execution"]["result"]["parameters_match"])
        self.assertIsNone(result["validation"])

    def test_validation_adapter_failure_is_persisted_and_retryable(self) -> None:
        class FlakyAdapter(SyntheticKafkaAdapter):
            def __init__(self) -> None:
                super().__init__()
                self.failures_remaining = 1

            def collect_after(self, incident_id: str, scenario: str):
                if self.failures_remaining:
                    self.failures_remaining -= 1
                    raise TimeoutError("synthetic timeout")
                return super().collect_after(incident_id, scenario)

        workflow = ReliabilityWorkflow(self.repository, adapter=FlakyAdapter())
        incident = workflow.investigate("consumer_slowdown")
        incident_id = incident["incident_id"]
        workflow.approve(incident_id, ApprovalRequest(
            approved=True, approved_by="test-operator", reason="exercise retry state"
        ))
        failed = workflow.execute_and_validate(incident_id)
        self.assertEqual("VALIDATION_FAILED", failed["status"])
        self.assertFalse(failed["validation"]["result"]["passed"])
        self.assertEqual({"adapter_available": False}, failed["validation"]["result"]["checks"])

        retried = workflow.execute_and_validate(incident_id)
        self.assertEqual("VALIDATED", retried["status"])
        self.assertTrue(retried["validation"]["result"]["passed"])


if __name__ == "__main__":
    unittest.main()
