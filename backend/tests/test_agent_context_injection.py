
import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock database before importing agent_core (because it is imported at top level)
sys.modules['database'] = MagicMock()
# Mock google to prevent import errors if not installed
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()

import agent_core
from agent_core import AgentCore

class TestAgentContextInjection(unittest.TestCase):
    def setUp(self):
        # Create fresh mocks
        self.mock_genai = MagicMock()
        self.mock_db_class = MagicMock()
        self.mock_db_instance = MagicMock()
        self.mock_db_class.return_value = self.mock_db_instance

        # Monkey patch agent_core globals
        agent_core.genai = self.mock_genai
        agent_core.FirestoreClient = self.mock_db_class
        agent_core.is_genai_configured = True

        # Mock environment
        self.original_env = dict(os.environ)
        os.environ['GOOGLE_API_KEY'] = 'fake-key'

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_context_injection_refactor(self):
        """
        Verifies that:
        1. system_instruction contains ONLY text.
        2. Files are passed in send_message payload.
        """
        # Setup Mock Files
        mock_file_persona = MagicMock()
        mock_file_persona.name = 'files/persona'
        mock_file_persona.state.name = 'ACTIVE'

        mock_file_knowledge = MagicMock()
        mock_file_knowledge.name = 'files/knowledge'
        mock_file_knowledge.state.name = 'ACTIVE'

        # Configure get_file side effect on the mock_genai we injected
        def get_file_side_effect(name):
            if name == 'files/persona':
                return mock_file_persona
            elif name == 'files/knowledge':
                return mock_file_knowledge
            return MagicMock()

        self.mock_genai.get_file.side_effect = get_file_side_effect

        # Mock Firestore to return these files
        self.mock_db_instance.get_knowledge_files.return_value = [
            {"name": "files/persona", "type": "persona"},
            {"name": "files/knowledge", "type": "knowledge"}
        ]

        # Mock Firestore config content to return strings (Crucial for string concatenation in agent_core)
        self.mock_db_instance.get_config_content.return_value = "MOCK_CONFIG_CONTENT"

        # Initialize Agent
        print("Initializing AgentCore with patched mocks...")
        agent = AgentCore()

        # Verify get_file calls
        print(f"get_file calls: {self.mock_genai.get_file.call_args_list}")

        # Verify GenerativeModel initialization
        self.mock_genai.GenerativeModel.assert_called()
        call_args = self.mock_genai.GenerativeModel.call_args
        kwargs = call_args[1]

        system_instruction = kwargs.get('system_instruction')

        # CHECK 1: system_instruction must be a list of strings or a single string
        if isinstance(system_instruction, list):
            for part in system_instruction:
                # With current BROKEN code, this will print active files if any
                # print(f"System Instruction Part Type: {type(part)}")
                if not isinstance(part, str):
                    print(f"FOUND NON-STRING PART: {part}")

        # Assertion (will fail until fixed)
        if isinstance(system_instruction, list):
            for part in system_instruction:
                self.assertIsInstance(part, str, f"Found non-string part in system_instruction: {part}")
        else:
            self.assertIsInstance(system_instruction, str)

        # CHECK 2: Files are injected in generate_response
        mock_chat = MagicMock()
        agent.model.start_chat.return_value = mock_chat

        user_msg = "Hello agent"
        history = []

        agent.generate_response(user_msg, history)

        # Verify send_message call arguments
        mock_chat.send_message.assert_called()
        send_args = mock_chat.send_message.call_args[0]
        payload = send_args[0]

        print(f"Send Message Payload: {payload}")

        self.assertIsInstance(payload, list, "Payload passed to send_message must be a list to include files")
        self.assertIn(user_msg, payload)
        self.assertIn(mock_file_persona, payload, "Persona file missing from message payload")
        self.assertIn(mock_file_knowledge, payload, "Knowledge file missing from message payload")

if __name__ == '__main__':
    unittest.main()
