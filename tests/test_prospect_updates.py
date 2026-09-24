import os
import unittest
from unittest.mock import patch

os.environ.setdefault("OPENAI_API_KEY", "test-key")

from gtm_agent import data_service
from gtm_agent.gtm_agent import build_prospect_profile, score_prospect


class _ScoringResult:
    def model_dump(self):
        return {
            "score": 100,
            "max_score": 100,
            "justification": "Okta is present.",
            "rubric_breakdown": {
                "revenue_fit": 100,
                "tech_stack_match": 100,
                "segment_fit": 100,
                "component_max": 100,
            },
        }


class _ScoringStub:
    def __init__(self):
        self.user_message = None

    def invoke(self, messages):
        self.user_message = messages[1]["content"]
        return _ScoringResult()


class ProspectUpdateTest(unittest.TestCase):
    prospect_id = "LEAD-12853"

    def setUp(self):
        self.original_stack = list(data_service.PROSPECTS[self.prospect_id]["tech_stack"])
        data_service._PROFILES.pop(self.prospect_id, None)

    def tearDown(self):
        data_service.PROSPECTS[self.prospect_id]["tech_stack"] = self.original_stack
        data_service._PROFILES.pop(self.prospect_id, None)

    def test_update_persists_and_refreshes_profile_for_scoring(self):
        build_prospect_profile.invoke(self.prospect_id)
        result = data_service.update_prospect_info(self.prospect_id, "Okta")
        profile = build_prospect_profile.invoke(self.prospect_id)["prospect_profile"]

        self.assertTrue(result["updated"])
        self.assertIn("Okta", data_service.fetch_tech_stack(self.prospect_id))
        self.assertIn("Okta", profile["tech_stack"])

        scoring_stub = _ScoringStub()
        with patch("gtm_agent.gtm_agent._scoring_llm", scoring_stub):
            score_prospect.invoke({
                "prospect_profile": profile,
                "offering": {
                    "required_tech_stack": ["Okta"],
                    "min_annual_revenue": 1,
                    "description": "Identity platform",
                },
            })

        self.assertIn('"Okta"', scoring_stub.user_message)
        self.assertNotIn('"missing"', scoring_stub.user_message.lower())


if __name__ == "__main__":
    unittest.main()
