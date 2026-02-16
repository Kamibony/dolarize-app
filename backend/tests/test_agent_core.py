import unittest
from unittest.mock import MagicMock, patch, ANY
import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Mock database module before importing agent_core to avoid real DB connection
sys.modules['database'] = MagicMock()
sys.modules['database'].FirestoreClient = MagicMock()

from backend.agent_core import AgentCore, SYSTEM_PROMPT

class TestAgentCore(unittest.TestCase):
    @patch('backend.agent_core.FirestoreClient')
    @patch('google.generativeai.GenerativeModel')
    def test_initialization(self, MockModel, MockFirestore):
        # We need to ensure AgentCore initializes with a model when configured
        with patch('backend.agent_core.is_genai_configured', True):
            agent = AgentCore()
            # It might be called with system_instruction list
            MockModel.assert_called()
            args, kwargs = MockModel.call_args
            self.assertEqual(kwargs['model_name'], 'gemini-2.5-flash')
            self.assertIsNotNone(agent.model)

    @patch('backend.agent_core.FirestoreClient')
    def test_initialization_failure(self, MockFirestore):
        # Test initialization when GenAI is not configured
        with patch('backend.agent_core.is_genai_configured', False):
             agent = AgentCore()
             self.assertIsNone(agent.model)

    def test_system_prompt_content(self):
        self.assertIn("André Digital", SYSTEM_PROMPT)
        self.assertIn("Calmo", SYSTEM_PROMPT)
        self.assertIn("BASE DE CONHECIMENTO", SYSTEM_PROMPT)

if __name__ == '__main__':
    unittest.main()
