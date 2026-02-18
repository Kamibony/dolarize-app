import google.generativeai as genai
from docx import Document
import os
import logging
from typing import Union, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FileParser:
    @staticmethod
    def parse_file(file_path: str, mime_type: str, display_name: Optional[str] = None) -> Union[str, genai.types.File]:
        """
        Parses a file based on its MIME type.

        If MIME is application/pdf or image/* -> Return as genai.types.File (Native support).
        If MIME is ...wordprocessingml.document (.docx) -> Use python-docx to extract text -> Return as String.
        If MIME is text/plain -> Read and return as String.
        """
        logger.info(f"Parsing file: {file_path} with mime_type: {mime_type}")

        if mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            try:
                doc = Document(file_path)
                full_text = []
                for para in doc.paragraphs:
                    if para.text.strip():  # Only add non-empty paragraphs
                        full_text.append(para.text)
                return "\n".join(full_text)
            except Exception as e:
                logger.error(f"Failed to parse DOCX: {str(e)}")
                raise ValueError(f"Failed to parse DOCX: {str(e)}")

        elif mime_type.startswith("text/") or mime_type == "text/plain":
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to read text file: {str(e)}")
                raise ValueError(f"Failed to read text file: {str(e)}")

        else:
            # Assume it's a file supported natively by Gemini (PDF, Images, etc.)
            try:
                if not display_name:
                    display_name = os.path.basename(file_path)
                # Ensure mime_type is passed correctly
                file_obj = genai.upload_file(path=file_path, mime_type=mime_type, display_name=display_name)
                logger.info(f"Uploaded file to Gemini: {file_obj.name}")
                return file_obj
            except Exception as e:
                logger.error(f"Failed to upload file to Gemini: {str(e)}")
                raise ValueError(f"Failed to upload file to Gemini: {str(e)}")
