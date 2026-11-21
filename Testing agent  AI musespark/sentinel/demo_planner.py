"""Phase 1 demo: 3 Salesforce stories -> TestCase JSON. Run: make demo."""

from __future__ import annotations

import json
import logging

from sentinel.agents.planner import plan
from sentinel.config import Settings
from sentinel.models import UserStory

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

STORIES = [
    UserStory(
        id="US-LEAD-001",
        title="Create a Lead and convert to Opportunity",
        description=(
            "As a sales rep I create a Lead with name, company, and email, "
            "convert it to an Opportunity, and mark it Closed Won."
        ),
        acceptance_criteria=[
            "Lead requires Last Name and Company; missing either blocks save with an error.",
            "Convert creates an Account + Opportunity linked to the Lead.",
            "Opportunity Stage can move to Closed Won with Amount > 0.",
        ],
    ),
    UserStory(
        id="US-OPP-002",
        title="Edit Opportunity amount and stage",
        description=(
            "As a sales rep I edit an existing Opportunity's Amount and Stage; "
            "validation requires Amount >= 0 and Stage from the picklist."
        ),
        acceptance_criteria=[
            "Negative amounts are rejected with a validation message.",
            "Stage changes persist after reload.",
            "Saving twice quickly creates only one update (no duplicate).",
        ],
    ),
    UserStory(
        id="US-CASE-003",
        title="Create a support Case from a Contact",
        description=(
            "As a support agent I create a Case from a Contact record with "
            "Subject, Priority, and Description; Subject is required."
        ),
        acceptance_criteria=[
            "Empty Subject blocks save with a visible error.",
            "Priority defaults to Medium.",
            "Case appears in the Contact's related list after save.",
        ],
    ),
]


def main() -> None:
    settings = Settings.from_env()
    print(f"Model: {settings.anthropic_model}")
    for story in STORIES:
        print(f"\n=== {story.id}: {story.title} ===")
        cases = plan(story, settings=settings)
        print(f"Produced {len(cases)} cases.")
        print(json.dumps([c.model_dump() for c in cases[:2]], indent=2))
        print(f"... ({len(cases) - 2} more, all schema-valid)" if len(cases) > 2 else "")


if __name__ == "__main__":
    main()
