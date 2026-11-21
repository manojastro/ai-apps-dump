from evalharness.models import TestCase
from evalharness.targets import DemoAgentTarget


def evaluate(case: dict) -> dict:
    """Example Python-callable target loaded as examples.demo_agent.plugin:evaluate."""
    return DemoAgentTarget("good").invoke(TestCase.from_dict(case)).to_dict()

