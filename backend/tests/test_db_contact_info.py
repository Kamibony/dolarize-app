import unittest
from unittest.mock import MagicMock, patch
from backend.database import FirestoreClient

class TestFirestoreClientContactInfo(unittest.TestCase):
    @patch('backend.database.firestore')
    @patch('backend.database.firebase_admin')
    def setUp(self, mock_firebase_admin, mock_firestore):
        # Mock firestore client
        self.mock_db = MagicMock()
        mock_firestore.client.return_value = self.mock_db
        self.client = FirestoreClient()

    def test_update_user_contact_info_name_only(self):
        user_id = "test_user_123"
        name = "João Teste"

        # Call the method
        self.client.update_user_contact_info(user_id, name=name)

        # Verify calls
        self.mock_db.collection.assert_called_with("usuarios")
        self.mock_db.collection().document.assert_called_with(user_id)
        self.mock_db.collection().document().set.assert_called_with(
            {"nome": name}, merge=True
        )

    def test_update_user_contact_info_email_only(self):
        user_id = "test_user_123"
        email = "joao@example.com"

        # Call the method
        self.client.update_user_contact_info(user_id, email=email)

        # Verify calls
        self.mock_db.collection().document().set.assert_called_with(
            {"email": email}, merge=True
        )

    def test_update_user_contact_info_both(self):
        user_id = "test_user_123"
        name = "João Teste"
        email = "joao@example.com"

        # Call the method
        self.client.update_user_contact_info(user_id, name=name, email=email)

        # Verify calls
        self.mock_db.collection().document().set.assert_called_with(
            {"nome": name, "email": email}, merge=True
        )

    def test_update_user_contact_info_none(self):
        user_id = "test_user_123"

        # Call the method with no updates
        self.client.update_user_contact_info(user_id)

        # Verify set was NOT called
        # We need to check if .set() was called on the document reference
        # Since we are mocking the chain, we check if the last set was called
        # But wait, if update_data is empty, set() is NOT called.

        # Reset mock to be sure
        self.mock_db.collection().document().set.reset_mock()

        self.client.update_user_contact_info(user_id)
        self.mock_db.collection().document().set.assert_not_called()

if __name__ == '__main__':
    unittest.main()
