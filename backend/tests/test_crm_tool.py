import unittest
from unittest.mock import MagicMock, patch
import contextvars
import sys
import os

# Ensure backend is in path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.agent_core import AgentCore, user_context

class TestLeadExtractionTool(unittest.TestCase):
    def setUp(self):
        # Patch dependencies
        self.patcher_firestore = patch('backend.agent_core.FirestoreClient')
        self.mock_firestore_cls = self.patcher_firestore.start()
        self.mock_db = self.mock_firestore_cls.return_value

        self.patcher_genai = patch('backend.agent_core.genai')
        self.mock_genai = self.patcher_genai.start()

        # Initialize agent
        self.agent = AgentCore()
        # Ensure db is set
        self.agent.db = self.mock_db

    def tearDown(self):
        self.patcher_firestore.stop()
        self.patcher_genai.stop()

    def test_extract_lead_info_success(self):
        # Set user context
        token = user_context.set("user_123")

        try:
            # Call tool
            result = self.agent.extract_lead_info(
                name="Carlos",
                email="carlos@example.com",
                pain_point="Inflação",
                profile_category="B_EM_CONSTRUCAO"
            )

            # Verify result
            self.assertEqual(result, "Informações do lead atualizadas com sucesso.")

            # Verify DB call
            self.mock_db.save_lead.assert_called_once()
            call_args = self.mock_db.save_lead.call_args[0][0]

            self.assertEqual(call_args["id"], "user_123")
            self.assertEqual(call_args["nome"], "Carlos")
            self.assertEqual(call_args["email"], "carlos@example.com")
            self.assertEqual(call_args["dor_principal"], "Inflação")
            self.assertEqual(call_args["classificacao_lead"], "B_EM_CONSTRUCAO")
            self.assertIsNone(call_args["telefone"])

        finally:
            user_context.reset(token)

    def test_extract_lead_info_no_context(self):
        # Ensure no context
        # user_context default is None
        # In case previous test failed to reset (though try/finally handles it), we set to None
        token = user_context.set(None)

        try:
            result = self.agent.extract_lead_info(name="Pedro")
            self.assertEqual(result, "Erro: Contexto do usuário não encontrado.")
            self.mock_db.save_lead.assert_not_called()
        finally:
             user_context.reset(token)

if __name__ == '__main__':
    unittest.main()
