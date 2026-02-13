import unittest
from unittest.mock import MagicMock
import sys
import os

# Add backend to path (backend is now 2 levels up relative to this file)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.agent_core import AgentCore, SYSTEM_PROMPT

class TestAgentCore(unittest.TestCase):
    def test_initialization(self):
        # Mock genai.GenerativeModel
        with unittest.mock.patch('google.generativeai.GenerativeModel') as mock_model:
            agent = AgentCore()
            self.assertIsNotNone(agent)
            mock_model.assert_called_with('gemini-pro')

    def test_system_prompt_content(self):
        self.assertIn("André Digital", SYSTEM_PROMPT)
        self.assertIn("Calmo", SYSTEM_PROMPT)
        self.assertIn("Seguro", SYSTEM_PROMPT)
        self.assertIn("Objetivo", SYSTEM_PROMPT)
        self.assertIn("Sem ansiedade", SYSTEM_PROMPT)
        self.assertIn("Conduzir mais. Explicar menos", SYSTEM_PROMPT)

if __name__ == '__main__':
    unittest.main()
