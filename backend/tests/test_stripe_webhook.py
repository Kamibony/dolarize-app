import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
import json
import os
import sys

# Mock imports
sys.modules['firebase_admin'] = MagicMock()
sys.modules['google.cloud'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()
sys.modules['stripe'] = MagicMock()

class TestStripeWebhook(unittest.TestCase):
    def setUp(self):
        self.env_patcher = patch.dict(os.environ, {
            "STRIPE_WEBHOOK_SECRET": "test_secret"
        })
        self.env_patcher.start()

        self.patch_db = patch('backend.database.FirestoreClient')
        self.mock_db_cls = self.patch_db.start()
        self.mock_db = self.mock_db_cls.return_value
        self.mock_db.get_user.return_value = {"id": "user123", "email": "test@example.com"}
        self.mock_db.update_user_status_by_email.return_value = True

        sys.path.append(os.path.abspath("backend"))
        from backend.routers import webhooks
        import stripe

        # Patch stripe
        stripe.Webhook.construct_event = MagicMock()

        self.webhooks = webhooks
        self.webhooks.db = self.mock_db
        self.stripe_mock = stripe

        self.app = FastAPI()
        self.app.include_router(webhooks.router)
        self.client = TestClient(self.app)

    def tearDown(self):
        self.env_patcher.stop()
        self.patch_db.stop()

    def test_stripe_webhook_with_client_reference_id(self):
        payload = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "client_reference_id": "user123",
                    "customer_details": {"email": "test@example.com"},
                    "metadata": {}
                }
            }
        }
        json_payload = json.dumps(payload)

        # Mock construct_event to return our payload object
        self.stripe_mock.Webhook.construct_event.return_value = payload

        response = self.client.post("/webhook/stripe", content=json_payload, headers={"Stripe-Signature": "sig"})
        self.assertEqual(response.status_code, 200)

        # Verify DB calls
        # process_stripe_event is async background task.
        # TestClient runs background tasks.
        # We need to verify db.save_user or db.get_user was called with "user123"
        # However, TestClient context might not wait for async bg tasks if not using AsyncClient?
        # Starlette TestClient runs background tasks synchronously.

        self.mock_db.get_user.assert_called_with("user123")
        self.mock_db.save_user.assert_called()

    def test_stripe_webhook_with_metadata_user_id(self):
        payload = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "client_reference_id": None,
                    "customer_details": {"email": "test@example.com"},
                    "metadata": {"user_id": "user456"}
                }
            }
        }
        # Mock DB for this user
        self.mock_db.get_user.return_value = {"id": "user456"}

        self.stripe_mock.Webhook.construct_event.return_value = payload

        response = self.client.post("/webhook/stripe", content=json.dumps(payload), headers={"Stripe-Signature": "sig"})
        self.assertEqual(response.status_code, 200)

        self.mock_db.get_user.assert_called_with("user456")
