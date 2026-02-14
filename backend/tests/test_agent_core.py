import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.agent_core import AgentCore, SYSTEM_PROMPT

class TestAgentCore(unittest.TestCase):
    def test_initialization(self):
        # We need to ensure AgentCore initializes with a model when configured
        with patch('backend.agent_core.is_genai_configured', True):
            # Mock genai.GenerativeModel
            with patch('google.generativeai.GenerativeModel') as MockModel:
                agent = AgentCore()
                MockModel.assert_called_with('gemini-2.5-flash')
                self.assertIsNotNone(agent.model)

    def test_initialization_failure(self):
        # Test initialization when GenAI is not configured
        with patch('backend.agent_core.is_genai_configured', False):
             agent = AgentCore()
             self.assertIsNone(agent.model)

    def test_system_prompt_content(self):
        self.assertIn("André Digital", SYSTEM_PROMPT)
        self.assertIn("Calmo", SYSTEM_PROMPT)
        self.assertIn("Segurança não é promessa", SYSTEM_PROMPT)
        self.assertIn("Conduzir mais. Explicar menos", SYSTEM_PROMPT)
        self.assertIn("LIMITES ABSOLUTOS", SYSTEM_PROMPT)
        self.assertIn("ÁRVORE DE DECISÃO INTERNA", SYSTEM_PROMPT)
        self.assertIn("Regular a ansiedade", SYSTEM_PROMPT)

if __name__ == '__main__':
    unittest.main()
