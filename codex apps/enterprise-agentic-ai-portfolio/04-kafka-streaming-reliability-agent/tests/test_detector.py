import unittest

from app.detector import DeterministicReasoner
from app.simulator import SCENARIOS, SyntheticKafkaAdapter


class DetectorTests(unittest.TestCase):
    def test_all_ground_truth_scenarios_are_classified(self) -> None:
        adapter = SyntheticKafkaAdapter()
        reasoner = DeterministicReasoner()
        for name, scenario in SCENARIOS.items():
            with self.subTest(scenario=name):
                diagnosis = reasoner.diagnose("inc-test", name, adapter.collect(name))
                self.assertEqual(scenario.root_cause, diagnosis.result.probable_root_cause)
                self.assertGreaterEqual(diagnosis.result.confidence, 0.9)
                self.assertGreaterEqual(len(diagnosis.result.evidence), 3)
                evidence_ids = {item.evidence_id for item in diagnosis.result.evidence}
                self.assertTrue(set(diagnosis.result.hypotheses[0].supporting_evidence_ids) <= evidence_ids)


if __name__ == "__main__":
    unittest.main()
