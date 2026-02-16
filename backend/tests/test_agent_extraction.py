import unittest
from unittest.mock import MagicMock, patch
import backend.agent_core

class TestAgentCoreExtraction(unittest.TestCase):
    def setUp(self):
        # Create patches
        self.patcher_genai = patch('backend.agent_core.genai')
        self.patcher_firestore = patch('backend.agent_core.FirestoreClient')
        self.patcher_config = patch('backend.agent_core.is_genai_configured', True)

        # Start patches
        self.mock_genai = self.patcher_genai.start()
        self.mock_firestore = self.patcher_firestore.start()
        self.patcher_config.start()

        # Setup mock model
        self.mock_model = MagicMock()
        self.mock_genai.GenerativeModel.return_value = self.mock_model

        # Initialize agent
        self.agent = backend.agent_core.AgentCore()

        # Ensure model is set (in case logic failed)
        self.agent.model = self.mock_model

    def tearDown(self):
        self.patcher_config.stop()
        self.patcher_firestore.stop()
        self.patcher_genai.stop()

    def test_extract_contact_info_json(self):
        # Mock response from Gemini
        mock_response = MagicMock()
        mock_response.text = '{"nome": "João", "email": "joao@email.com"}'
        self.mock_model.generate_content.return_value = mock_response

        result = self.agent.extract_contact_info("Meu nome é João e meu email é joao@email.com")

        self.assertEqual(result, {"nome": "João", "email": "joao@email.com"})

    def test_extract_contact_info_markdown_json(self):
        # Mock response with markdown code block
        mock_response = MagicMock()
        mock_response.text = '```json\n{"nome": "Maria", "email": null}\n```'
        self.mock_model.generate_content.return_value = mock_response

        result = self.agent.extract_contact_info("Sou a Maria")

        self.assertEqual(result, {"nome": "Maria", "email": None})

    def test_extract_contact_info_error(self):
        # Mock exception
        self.mock_model.generate_content.side_effect = Exception("API Error")

        result = self.agent.extract_contact_info("Mensagem")

        self.assertEqual(result, {})

if __name__ == '__main__':
    unittest.main()
