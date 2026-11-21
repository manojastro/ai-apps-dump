import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.client = TestClient(create_app(Path(self.temp_dir.name) / "api.db"))

    def tearDown(self) -> None:
        self.client.close()
        self.temp_dir.cleanup()

    def test_health_readiness_metrics_and_dashboard(self) -> None:
        self.assertEqual(200, self.client.get("/health").status_code)
        self.assertEqual("ready", self.client.get("/ready").json()["status"])
        self.assertIn("kafka_agent_rca_accuracy", self.client.get("/metrics").text)
        self.assertIn("StreamSentinel", self.client.get("/").text)

    def test_full_incident_api_workflow(self) -> None:
        created = self.client.post("/api/v1/scenarios/malformed_message/inject")
        self.assertEqual(201, created.status_code)
        incident_id = created.json()["incident_id"]

        blocked = self.client.post(f"/api/v1/incidents/{incident_id}/execute")
        self.assertEqual(409, blocked.status_code)

        approved = self.client.post(f"/api/v1/incidents/{incident_id}/approval", json={
            "approved": True, "approved_by": "api-test", "reason": "evidence reviewed"
        })
        self.assertEqual("APPROVED", approved.json()["status"])

        executed = self.client.post(f"/api/v1/incidents/{incident_id}/execute")
        self.assertEqual(200, executed.status_code)
        self.assertEqual("VALIDATED", executed.json()["status"])
        self.assertTrue(executed.json()["validation"]["result"]["passed"])

        evaluation = self.client.get("/api/v1/evaluations/summary").json()
        self.assertEqual(1.0, evaluation["rca_accuracy"])

    def test_unknown_scenario_is_rejected(self) -> None:
        self.assertEqual(404, self.client.post("/api/v1/scenarios/not-real/inject").status_code)

    def test_secure_mode_separates_viewer_approver_and_executor(self) -> None:
        with tempfile.TemporaryDirectory() as secure_dir, patch.dict("os.environ", {
            "AUTH_MODE": "api_key",
            "API_KEY": "viewer-key",
            "APPROVER_API_KEY": "approver-key",
            "EXECUTOR_API_KEY": "executor-key",
        }, clear=False):
            secure_client = TestClient(create_app(Path(secure_dir) / "secure.db"))
            try:
                created = secure_client.post(
                    "/api/v1/scenarios/consumer_slowdown/inject", headers={"X-API-Key": "viewer-key"}
                )
                self.assertEqual(201, created.status_code)
                incident_id = created.json()["incident_id"]
                approval_body = {"approved": True, "approved_by": "spoofed-user", "reason": "reviewed evidence"}
                viewer_denied = secure_client.post(
                    f"/api/v1/incidents/{incident_id}/approval", json=approval_body,
                    headers={"X-API-Key": "viewer-key"},
                )
                self.assertEqual(403, viewer_denied.status_code)
                approved = secure_client.post(
                    f"/api/v1/incidents/{incident_id}/approval", json=approval_body,
                    headers={"X-API-Key": "approver-key"},
                )
                self.assertEqual("authenticated-approver", approved.json()["approval"]["approved_by"])
                executor_denied = secure_client.post(
                    f"/api/v1/incidents/{incident_id}/execute", headers={"X-API-Key": "approver-key"}
                )
                self.assertEqual(403, executor_denied.status_code)
                executed = secure_client.post(
                    f"/api/v1/incidents/{incident_id}/execute", headers={"X-API-Key": "executor-key"}
                )
                self.assertEqual("VALIDATED", executed.json()["status"])
            finally:
                secure_client.close()


if __name__ == "__main__":
    unittest.main()
