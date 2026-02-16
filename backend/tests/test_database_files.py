import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# We need to mock firebase_admin before importing database
with patch('firebase_admin.credentials'), patch('firebase_admin.initialize_app'):
    from database import FirestoreClient

class TestDatabaseFiles(unittest.TestCase):
    def setUp(self):
        # Mock firestore client
        self.mock_firestore_patcher = patch('database.firestore')
        self.mock_firestore = self.mock_firestore_patcher.start()
        self.mock_client = MagicMock()
        self.mock_firestore.client.return_value = self.mock_client

        # Initialize DB
        self.db = FirestoreClient()

    def tearDown(self):
        self.mock_firestore_patcher.stop()

    def test_add_knowledge_file_default(self):
        file_data = {"name": "test.txt"}
        # Mock add return value
        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "doc123"
        self.mock_client.collection.return_value.add.return_value = (None, mock_doc_ref)

        doc_id = self.db.add_knowledge_file(file_data)

        self.assertEqual(doc_id, "doc123")
        # Verify call args
        # db.collection(...).add(...)
        args, _ = self.mock_client.collection.return_value.add.call_args
        saved_data = args[0]
        self.assertEqual(saved_data["type"], "knowledge")

    def test_add_knowledge_file_persona(self):
        file_data = {"name": "persona.txt"}
        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "doc456"
        self.mock_client.collection.return_value.add.return_value = (None, mock_doc_ref)

        doc_id = self.db.add_knowledge_file(file_data, file_type="persona")

        args, _ = self.mock_client.collection.return_value.add.call_args
        saved_data = args[0]
        self.assertEqual(saved_data["type"], "persona")

    def test_get_knowledge_files_filter(self):
        # Mock query stream
        mock_docs = []

        # Doc 1: Knowledge (implicit)
        doc1 = MagicMock()
        doc1.id = "1"
        doc1.to_dict.return_value = {"name": "k1.txt"} # no type
        mock_docs.append(doc1)

        # Doc 2: Knowledge (explicit)
        doc2 = MagicMock()
        doc2.id = "2"
        doc2.to_dict.return_value = {"name": "k2.txt", "type": "knowledge"}
        mock_docs.append(doc2)

        # Doc 3: Persona
        doc3 = MagicMock()
        doc3.id = "3"
        doc3.to_dict.return_value = {"name": "p1.txt", "type": "persona"}
        mock_docs.append(doc3)

        # Mock the chain: collection -> order_by -> stream
        # The code does: self.db.collection("knowledge_base").order_by(...).stream()
        self.mock_client.collection.return_value.order_by.return_value.stream.return_value = mock_docs

        # Test 1: Get All (implicitly filtered? No, get_knowledge_files without arg returns all?)
        # My implementation: if file_type is None, returns all.
        files = self.db.get_knowledge_files(file_type=None)
        self.assertEqual(len(files), 3)
        self.assertEqual(files[0]["type"], "knowledge") # Defaulted
        self.assertEqual(files[2]["type"], "persona")

        # Test 2: Get Knowledge
        files_k = self.db.get_knowledge_files(file_type="knowledge")
        self.assertEqual(len(files_k), 2) # doc1 and doc2
        self.assertEqual(files_k[0]["id"], "1")
        self.assertEqual(files_k[1]["id"], "2")

        # Test 3: Get Persona
        files_p = self.db.get_knowledge_files(file_type="persona")
        self.assertEqual(len(files_p), 1)
        self.assertEqual(files_p[0]["id"], "3")

if __name__ == '__main__':
    unittest.main()
