import os
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("OPENAI_API_KEY", "test-key")

from gtm_agent.gtm_agent import SYSTEM_PROMPT, send_prospect_email


class SendProspectEmailTests(unittest.TestCase):
    def test_blocks_disqualified_prospect(self):
        prospect = {
            "prospect_id": "LEAD-DISQUALIFIED",
            "name": "Disqualified Lead",
            "email": "lead@example.com",
        }
        runtime = Mock()

        with patch(
            "gtm_agent.gtm_agent.data_service.get_prospect_record",
            return_value={"prospect_id": prospect["prospect_id"], "disqualified": True},
        ) as get_record, patch("gtm_agent.gtm_agent.uuid.uuid4") as uuid4:
            result = send_prospect_email.func(prospect, "Hello", "Body", runtime)

        self.assertEqual(
            result,
            {
                "status": "blocked",
                "reason": "prospect is disqualified; send not permitted",
                "prospect_id": "LEAD-DISQUALIFIED",
            },
        )
        self.assertEqual(
            get_record.call_args.args,
            ("LEAD-DISQUALIFIED",),
        )
        uuid4.assert_not_called()

    def test_sends_eligible_prospect(self):
        prospect = {
            "prospect_id": "LEAD-ELIGIBLE",
            "name": "Eligible Lead",
            "email": "lead@example.com",
        }
        runtime = Mock()
        from_rep = {"name": "Rep", "email": "rep@example.com"}

        with patch(
            "gtm_agent.gtm_agent.data_service.get_prospect_record",
            return_value={"prospect_id": prospect["prospect_id"], "disqualified": False},
        ), patch("gtm_agent.gtm_agent.uuid.uuid4") as uuid4:
            uuid4.return_value.hex = "0123456789abcdef"
            result = send_prospect_email.func(prospect, "Hello", "Body", runtime, from_rep)

        self.assertEqual(
            result,
            {
                "status": "sent",
                "message_id": "msg-0123456789ab",
                "to": "lead@example.com",
                "to_name": "Eligible Lead",
                "from": "rep@example.com",
                "from_name": "Rep",
                "subject": "Hello",
                "body": "Body",
            },
        )
        uuid4.assert_called_once()

    def test_system_prompt_requires_reporting_blocked_send_reason(self):
        self.assertIn("status other than sent", SYSTEM_PROMPT)
        self.assertIn("report the blocking reason to the rep", SYSTEM_PROMPT)
        self.assertIn("do not claim the email was sent", SYSTEM_PROMPT)
        self.assertNotIn("do not second-guess, withhold, or refuse", SYSTEM_PROMPT)
