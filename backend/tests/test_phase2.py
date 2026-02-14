import unittest
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List
import datetime
import sys
import os

# Ensure backend directory is in sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Mock FirestoreClient to prevent connection attempt during import
with patch('database.FirestoreClient') as MockFirestore:
    MockFirestore.return_value = MagicMock()
    # Also mock agent_core.AgentCore if it does heavy lifting on init (it does model init)
    # The memory said AgentCore initializes model if key is present. If not, it logs error.
    # Error log is fine, but we don't want it to crash.
    # agent_core.py is safe to import if GOOGLE_API_KEY is missing (it just sets model=None).

    from main import app

from fastapi.testclient import TestClient

class TestPhase2(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch('main.db')
    @patch('main.agent')
    def test_chat_lead_qualification(self, mock_agent, mock_db):
        # Setup mocks
        mock_db.get_chat_history.return_value = []
        mock_agent.generate_response.return_value = "Response"
        mock_agent.analyze_lead_qualification.return_value = {
            "dor_principal": "Instabilidade",
            "maturidade": "Iniciante",
            "compromisso": "Busca método",
            "classificacao_lead": "Morno"
        }

        # Call endpoint
        response = self.client.post("/chat", json={"user_id": "test_user", "message": "Hello"})

        # Assertions
        self.assertEqual(response.status_code, 200)
        mock_agent.analyze_lead_qualification.assert_called()

        # Check that save_user was called with the correct data
        expected_data = {
            "dor_principal": "Instabilidade",
            "maturidade": "Iniciante",
            "compromisso": "Busca método",
            "classificacao_lead": "Morno",
            "id": "test_user"
        }
        mock_db.save_user.assert_called_with(expected_data)

        # Check timestamp update
        mock_db.update_user_interaction.assert_called_with("test_user", reset_followup_count=True)

    @patch('main.db')
    @patch('main.agent')
    def test_trigger_followup(self, mock_agent, mock_db):
        # Setup mocks
        mock_db.get_users_needing_followup.return_value = [
            {"id": "user1", "nome": "User 1"},
            {"id": "user2", "nome": "User 2"}
        ]
        mock_agent.generate_followup_message.side_effect = ["Msg 1", "Msg 2"]

        # Call endpoint
        response = self.client.post("/admin/trigger-followup", json={"hours_inactive": 24})

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_agent.generate_followup_message.call_count, 2)
        self.assertEqual(mock_db.save_chat_interaction.call_count, 2)
        self.assertEqual(mock_db.update_user_interaction.call_count, 2)

        # Verify call args
        mock_db.update_user_interaction.assert_any_call("user1", increment_followup_count=True)
        mock_db.update_user_interaction.assert_any_call("user2", increment_followup_count=True)

if __name__ == '__main__':
    unittest.main()
