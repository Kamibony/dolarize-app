import pytest
from unittest.mock import MagicMock, patch, mock_open
import sys
import os

# Ensure backend is in path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from utils import FileParser

@pytest.fixture
def mock_genai():
    with patch('utils.genai') as mock:
        yield mock

@pytest.fixture
def mock_docx():
    with patch('utils.Document') as mock:
        yield mock

def test_parse_docx(mock_docx):
    # Setup mock document
    mock_doc = MagicMock()
    p1 = MagicMock()
    p1.text = "Hello World"
    p2 = MagicMock()
    p2.text = "Second Paragraph"
    mock_doc.paragraphs = [p1, p2]
    mock_docx.return_value = mock_doc

    # Call parser
    result = FileParser.parse_file("dummy.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    # Verify
    assert result == "Hello World\nSecond Paragraph"
    mock_docx.assert_called_once_with("dummy.docx")

def test_parse_text():
    content = "This is a text file."
    with patch("builtins.open", mock_open(read_data=content)) as mock_file:
        result = FileParser.parse_file("dummy.txt", "text/plain")
        assert result == content
        mock_file.assert_called_once_with("dummy.txt", "r", encoding="utf-8", errors="ignore")

def test_parse_pdf_upload(mock_genai):
    # Setup mock upload
    mock_file = MagicMock()
    mock_file.name = "files/123"
    mock_genai.upload_file.return_value = mock_file

    # Call parser
    result = FileParser.parse_file("dummy.pdf", "application/pdf", display_name="Contract.pdf")

    # Verify
    assert result == mock_file
    mock_genai.upload_file.assert_called_once()
    args, kwargs = mock_genai.upload_file.call_args
    assert kwargs['path'] == "dummy.pdf"
    assert kwargs['mime_type'] == "application/pdf"
    assert kwargs['display_name'] == "Contract.pdf"

def test_parse_pdf_upload_no_display_name(mock_genai):
    # Setup mock upload
    mock_file = MagicMock()
    mock_file.name = "files/123"
    mock_genai.upload_file.return_value = mock_file

    # Call parser
    result = FileParser.parse_file("dummy.pdf", "application/pdf")

    # Verify
    assert result == mock_file
    mock_genai.upload_file.assert_called_once()
    args, kwargs = mock_genai.upload_file.call_args
    assert kwargs['path'] == "dummy.pdf"
    assert kwargs['mime_type'] == "application/pdf"
    assert kwargs['display_name'] == "dummy.pdf" # basename fallback
