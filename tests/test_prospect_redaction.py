import os
import unittest

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ["LANGSMITH_TRACING"] = "false"

from gtm_agent import data_service
from gtm_agent.gtm_agent import build_prospect_profile, get_prospect


class ProspectRedactionTest(unittest.TestCase):
    prospect_id = "LEAD-12853"

    def setUp(self):
        data_service._PROFILES.clear()

    def test_tools_exclude_billing_fields(self):
        sensitive_fields = {"billing_qualification", "card_on_file", "tax_id", "date_of_birth"}

        contact_result = get_prospect.invoke({"prospect_id": self.prospect_id})
        profile_result = build_prospect_profile.invoke({"prospect_id": self.prospect_id})

        self.assertTrue(sensitive_fields.isdisjoint(contact_result["prospect"]))
        self.assertTrue(sensitive_fields.isdisjoint(profile_result["prospect_profile"]))
        self.assertTrue(sensitive_fields.isdisjoint(data_service._PROFILES[self.prospect_id]))


if __name__ == "__main__":
    unittest.main()
