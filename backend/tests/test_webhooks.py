import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
import hashlib
import hmac
import json
import sys
import os

# Set up mocks for external dependencies before imports
sys.modules['firebase_admin'] = MagicMock()
sys.modules['firebase_admin.credentials'] = MagicMock()
sys.modules['firebase_admin.firestore'] = MagicMock()
sys.modules['google.cloud'] = MagicMock()
sys.modules['google.cloud.firestore'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()

# Mock AgentCore dependencies
with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
    # We delay import until inside setUp or use patch
    pass

class TestWebhooks(unittest.TestCase):
    def setUp(self):
        # Patch environment variables
        self.env_patcher = patch.dict(os.environ, {
            "META_VERIFY_TOKEN": "test_token",
            "META_APP_SECRET": "test_secret",
            "META_ACCESS_TOKEN": "test_access",
            "META_PHONE_NUMBER_ID": "123456",
            "GOOGLE_API_KEY": "test_key"
        })
        self.env_patcher.start()

        # Patch FirestoreClient class
        self.patch_db = patch('backend.database.FirestoreClient')
        self.mock_db_cls = self.patch_db.start()
        self.mock_db_instance = self.mock_db_cls.return_value
        self.mock_db_instance.get_chat_history.return_value = []
        self.mock_db_instance.save_chat_interaction.return_value = "doc_id"
        self.mock_db_instance.update_user_interaction.return_value = None
        self.mock_db_instance.save_user.return_value = "user_id"

        # Patch MetaService
        self.patch_meta = patch('backend.services.meta_service.MetaService')
        self.mock_meta_cls = self.patch_meta.start()
        self.mock_meta_instance = self.mock_meta_cls.return_value
        self.mock_meta_instance.send_whatsapp_message = AsyncMock()
        self.mock_meta_instance.send_instagram_message = AsyncMock()

        # Patch AgentCore
        self.patch_agent = patch('backend.agent_core.AgentCore')
        self.mock_agent_cls = self.patch_agent.start()
        self.mock_agent_instance = self.mock_agent_cls.return_value
        self.mock_agent_instance.format_history.return_value = []
        self.mock_agent_instance.generate_response.return_value = "AI Response"
        self.mock_agent_instance.analyze_lead_qualification.return_value = {}

        # Import router now
        # We need to make sure backend is in path
        sys.path.append(os.path.abspath("backend"))
        from backend.routers import webhooks
        self.webhooks = webhooks

        # Inject mocks into webhooks module explicitly if needed
        # But patching classes usually handles instances created inside.
        # However, `webhooks.py` instantiates `db = FirestoreClient()` at module level.
        # Since we patched FirestoreClient before import (hopefully), `webhooks.db` should be our mock.
        # Wait, I imported webhooks inside setUp. But if it was already imported by another test or main, patching won't work on module level var.
        # So I should force reload or patch the module attribute.

        self.webhooks.db = self.mock_db_instance
        self.webhooks.meta_service = self.mock_meta_instance
        self.webhooks.agent = self.mock_agent_instance

        # Setup FastAPI app for testing router
        self.app = FastAPI()
        self.app.include_router(webhooks.router)
        self.client = TestClient(self.app)

    def tearDown(self):
        self.env_patcher.stop()
        self.patch_db.stop()
        self.patch_meta.stop()
        self.patch_agent.stop()

    def test_verify_webhook_success(self):
        response = self.client.get("/webhook/meta", params={
            "hub.mode": "subscribe",
            "hub.verify_token": "test_token",
            "hub.challenge": "12345"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "12345") # Plain text

    def test_verify_webhook_failure(self):
        response = self.client.get("/webhook/meta", params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token",
            "hub.challenge": "12345"
        })
        self.assertEqual(response.status_code, 403)

    def test_receive_webhook_invalid_signature(self):
        payload = {"object": "whatsapp_business_account", "entry": []}
        json_payload = json.dumps(payload)

        # Wrong signature
        headers = {"X-Hub-Signature-256": "sha256=invalid"}

        response = self.client.post("/webhook/meta", content=json_payload, headers=headers)
        self.assertEqual(response.status_code, 403)

    def test_receive_webhook_success(self):
        payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "5511999999999",
                            "type": "text",
                            "text": {"body": "Hello"}
                        }]
                    }
                }]
            }]
        }
        json_payload = json.dumps(payload)

        # Calculate correct signature
        secret = "test_secret".encode('utf-8')
        signature = hmac.new(secret, json_payload.encode('utf-8'), hashlib.sha256).hexdigest()
        headers = {"X-Hub-Signature-256": f"sha256={signature}"}

        # We patch process_meta_payload to verify it gets called
        with patch('backend.routers.webhooks.process_meta_payload', new_callable=AsyncMock) as mock_process:
            response = self.client.post("/webhook/meta", content=json_payload, headers=headers)
            self.assertEqual(response.status_code, 200)
            # The background task should be added. TestClient triggers background tasks.
            # However, TestClient implementation of background tasks is synchronous.
            # But process_meta_payload is async.
            # FastAPI's TestClient runs background tasks.
            # Let's see if mock_process is called.

            # Wait, since process_meta_payload is async, TestClient might not await it?
            # Actually TestClient uses Starlette's TestClient which handles background tasks.

            # If this fails, we can assume integration logic is tricky to test with mocks this way.
            # But let's try.
            # mock_process.assert_called_once()
            # (assert_called_once matches args too, but we just check called)
            self.assertTrue(mock_process.called)

if __name__ == '__main__':
    unittest.main()
