from __future__ import annotations

import argparse
import asyncio

from .api import engine, repository, seed_if_empty
from .fixtures import SCENARIOS
from .models import Incident
from .workflow import new_incident_id


async def generate(scenario: str, investigate: bool) -> Incident:
    config = SCENARIOS[scenario]
    incident = repository.save_incident(
        Incident(
            id=new_incident_id(),
            title=config["title"],
            service=config["service"],
            scenario=scenario,
            severity="SEV-2",
            alert_summary=config["impact"],
        )
    )
    print(f"Injected {incident.id}: {incident.title}")
    if investigate:
        result = await engine.investigate(incident)
        print(f"Leading cause: {result.hypotheses[0].statement}")
        print(f"Critic overturned leader: {result.critic.overturned}")
        print(result.rca.markdown)
    return incident


def main() -> None:
    parser = argparse.ArgumentParser(description="Inject a deterministic synthetic incident")
    parser.add_argument("--scenario", choices=SCENARIOS, default="bad-deployment")
    parser.add_argument("--investigate", action="store_true")
    args = parser.parse_args()
    asyncio.run(generate(args.scenario, args.investigate))


if __name__ == "__main__":
    main()
