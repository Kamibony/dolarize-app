import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Ensure backend is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database import FirestoreClient

class TestFirestoreClient(unittest.TestCase):

    def setUp(self):
        # Start patches
        self.patcher_fa = patch("backend.database.firebase_admin")
        self.patcher_fs = patch("backend.database.firestore")

        self.mock_firebase_admin = self.patcher_fa.start()
        self.mock_firestore = self.patcher_fs.start()

        # Setup mock db
        self.mock_db = MagicMock()
        self.mock_firestore.client.return_value = self.mock_db

        # Simulate no apps initialized
        self.mock_firebase_admin._apps = {}

        # Create a default client for most tests
        self.client = FirestoreClient()

    def tearDown(self):
        self.patcher_fa.stop()
        self.patcher_fs.stop()

    def test_init_with_service_account(self):
        # Reset mock to verify specific call
        self.mock_firebase_admin.initialize_app.reset_mock()
        self.mock_firebase_admin._apps = {}

        with patch("os.path.exists", return_value=True), \
             patch("backend.database.credentials.Certificate") as mock_cert:

            client = FirestoreClient(service_account_path="path/to/key.json")

            mock_cert.assert_called_with("path/to/key.json")
            self.mock_firebase_admin.initialize_app.assert_called()

    def test_save_user(self):
        user_data = {
            "id": "user123",
            "nome": "Test User",
            "telefone": "+5511999999999"
        }

        # Mock the document reference
        mock_doc_ref = MagicMock()
        self.mock_db.collection.return_value.document.return_value = mock_doc_ref

        # Call the method
        result = self.client.save_user(user_data)

        # Assertions
        self.mock_db.collection.assert_called_with("usuarios")
        self.mock_db.collection.return_value.document.assert_called_with("user123")
        mock_doc_ref.set.assert_called_with(user_data, merge=True)
        self.assertEqual(result, "user123")

    def test_save_user_missing_id(self):
        user_data = {"nome": "No ID"}
        with self.assertRaises(ValueError):
            self.client.save_user(user_data)

    def test_get_user(self):
        # Mock document snapshot
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"id": "user123", "nome": "Test User"}

        self.mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        result = self.client.get_user("user123")

        self.assertEqual(result, {"id": "user123", "nome": "Test User"})
        self.mock_db.collection.assert_called_with("usuarios")

    def test_get_user_not_found(self):
        mock_doc = MagicMock()
        mock_doc.exists = False

        self.mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        result = self.client.get_user("user123")
        self.assertIsNone(result)

    def test_save_chat_interaction(self):
        interaction_data = {
            "id_usuario": "user123",
            "timestamp": "2024-01-01T00:00:00Z",
            "mensagens": []
        }

        # Mock add return value (timestamp, doc_ref)
        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "chat123"
        self.mock_db.collection.return_value.add.return_value = (None, mock_doc_ref)

        result = self.client.save_chat_interaction(interaction_data)

        self.mock_db.collection.assert_called_with("interacoes_chat")
        self.mock_db.collection.return_value.add.assert_called_with(interaction_data)
        self.assertEqual(result, "chat123")

    def test_get_chat_history(self):
        mock_query = MagicMock()
        mock_doc1 = MagicMock()
        mock_doc1.to_dict.return_value = {"id": "1"}
        mock_doc2 = MagicMock()
        mock_doc2.to_dict.return_value = {"id": "2"}

        mock_query.stream.return_value = [mock_doc1, mock_doc2]

        # Chain mocking
        self.mock_db.collection.return_value.where.return_value.order_by.return_value.limit.return_value = mock_query

        result = self.client.get_chat_history("user123", limit=5)

        self.assertEqual(len(result), 2)
        # Verify collection call
        self.mock_db.collection.assert_called_with("interacoes_chat")
        # Verify call chain was initiated
        self.mock_db.collection.return_value.where.assert_called()

    def test_save_lesson_progress_new(self):
        progress_data = {
            "id_usuario": "user123",
            "modulo": "Mod1",
            "aula": "Aula1",
            "status": "concluido"
        }

        # Mock query returning empty list (no existing record)
        # collection() -> where() -> where() -> where()

        col_ref = self.mock_db.collection.return_value
        q1 = col_ref.where.return_value
        q2 = q1.where.return_value
        q3 = q2.where.return_value
        q3.stream.return_value = []

        self.client.save_lesson_progress(progress_data)

        # Verify add was called on collection ref
        col_ref.add.assert_called_with(progress_data)

    def test_save_lesson_progress_update(self):
        progress_data = {
            "id_usuario": "user123",
            "modulo": "Mod1",
            "aula": "Aula1",
            "status": "concluido"
        }

        # Mock query returning existing document
        mock_doc = MagicMock()
        mock_doc.reference = MagicMock()

        # Mock the chain
        col_ref = self.mock_db.collection.return_value
        q1 = col_ref.where.return_value
        q2 = q1.where.return_value
        q3 = q2.where.return_value
        q3.stream.return_value = [mock_doc] # Found existing

        self.client.save_lesson_progress(progress_data)

        mock_doc.reference.set.assert_called_with(progress_data, merge=True)
        col_ref.add.assert_not_called()

    def test_get_all_users(self):
        mock_doc1 = MagicMock()
        mock_doc1.id = "user1"
        mock_doc1.to_dict.return_value = {"nome": "User 1"}

        mock_doc2 = MagicMock()
        mock_doc2.id = "user2"
        mock_doc2.to_dict.return_value = {"nome": "User 2"}

        self.mock_db.collection.return_value.stream.return_value = [mock_doc1, mock_doc2]

        users = self.client.get_all_users()
        self.assertEqual(len(users), 2)
        self.assertEqual(users[0]["id"], "user1")
        self.mock_db.collection.assert_called_with("usuarios")

    def test_update_user_interaction(self):
        user_id = "user123"
        self.client.update_user_interaction(user_id)

        self.mock_db.collection.assert_called_with("usuarios")
        self.mock_db.collection.return_value.document.assert_called_with(user_id)
        # Check set call
        args, kwargs = self.mock_db.collection.return_value.document.return_value.set.call_args
        self.assertIn("last_interaction_timestamp", args[0])
        self.assertEqual(kwargs["merge"], True)

    def test_get_users_needing_followup(self):
        # Mock query
        mock_query = MagicMock()

        mock_doc1 = MagicMock()
        mock_doc1.id = "user1"
        mock_doc1.to_dict.return_value = {"nome": "Inactive User"}

        mock_query.stream.return_value = [mock_doc1]

        self.mock_db.collection.return_value.where.return_value = mock_query

        users = self.client.get_users_needing_followup(hours_inactive=24)

        self.assertEqual(len(users), 1)
        self.assertEqual(users[0]["id"], "user1")
        self.mock_db.collection.assert_called_with("usuarios")
        self.mock_db.collection.return_value.where.assert_called()

if __name__ == '__main__':
    unittest.main()
