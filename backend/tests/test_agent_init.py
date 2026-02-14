import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.agent_core import initialize_genai

class TestAgentInit(unittest.TestCase):
    @patch('backend.agent_core.genai')
    def test_initialize_genai_clean_key(self, mock_genai):
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "AIzaSyCleanKey"}):
            success = initialize_genai()
            self.assertTrue(success)
            mock_genai.configure.assert_called_with(api_key="AIzaSyCleanKey")

    @patch('backend.agent_core.genai')
    def test_initialize_genai_whitespace(self, mock_genai):
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "  AIzaSyWhitespace  "}):
            success = initialize_genai()
            self.assertTrue(success)
            mock_genai.configure.assert_called_with(api_key="AIzaSyWhitespace")

    @patch('backend.agent_core.genai')
    def test_initialize_genai_double_quotes(self, mock_genai):
        with patch.dict(os.environ, {"GOOGLE_API_KEY": '"AIzaSyDoubleQuotes"'}):
            success = initialize_genai()
            self.assertTrue(success)
            mock_genai.configure.assert_called_with(api_key="AIzaSyDoubleQuotes")

    @patch('backend.agent_core.genai')
    def test_initialize_genai_single_quotes(self, mock_genai):
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "'AIzaSySingleQuotes'"}):
            success = initialize_genai()
            self.assertTrue(success)
            mock_genai.configure.assert_called_with(api_key="AIzaSySingleQuotes")

    @patch('backend.agent_core.genai')
    def test_initialize_genai_mixed(self, mock_genai):
        with patch.dict(os.environ, {"GOOGLE_API_KEY": ' " AIzaSyMixed " '}):
            success = initialize_genai()
            self.assertTrue(success)
            mock_genai.configure.assert_called_with(api_key="AIzaSyMixed")

    @patch('backend.agent_core.genai')
    def test_initialize_genai_no_key(self, mock_genai):
        with patch.dict(os.environ, {}, clear=True):
            success = initialize_genai()
            self.assertFalse(success)
            mock_genai.configure.assert_not_called()

if __name__ == '__main__':
    unittest.main()
