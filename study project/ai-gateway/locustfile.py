"""Locust stub: measures gateway overhead (mock provider, offline).

Run: locust -f locustfile.py --headless -u 10 -r 2 -t 60s --host http://localhost:8000
Write p50/p95 gateway overhead into reports/load.json (see placeholder).
"""

from locust import HttpUser, between, task


class GatewayUser(HttpUser):
    wait_time = between(0.1, 0.5)

    def on_start(self) -> None:
        # Create/reuse a tenant out-of-band; paste key into GW_API_KEY env.
        import os

        self.key = os.getenv("GW_API_KEY", "sk-gw-dev")
        self.headers = {"Authorization": f"Bearer {self.key}", "X-Task": "triage"}

    @task
    def chat(self) -> None:
        self.client.post("/v1/chat/completions",
                         json={"model": "triage-cheap",
                               "messages": [{"role": "user",
                                             "content": "load test ping"}]},
                         headers=self.headers, name="/v1/chat/completions")
