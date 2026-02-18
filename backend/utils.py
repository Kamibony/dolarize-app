import google.generativeai as genai
from docx import Document
import os
import logging
from typing import Union, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants for Supported MIME Types
GEMINI_SUPPORTED_MIME_TYPES = [
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
    "video/mp4",
    "video/mpeg",
    "video/mov",
    "video/avi",
    "video/x-flv",
    "video/mpg",
    "video/webm",
    "video/wmv",
    "video/3gpp",
    "audio/wav",
    "audio/mp3",
    "audio/aiff",
    "audio/aac",
    "audio/ogg",
    "audio/flac"
]

TEXT_MIME_TYPES = [
    "application/json",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
]

class FileParser:
    @staticmethod
    def parse_file(file_path: str, mime_type: str, display_name: Optional[str] = None) -> Union[str, genai.types.File]:
        """
        Parses a file based on its MIME type.

        Routing Logic:
        1. Text Assets (.docx, .txt, .md, .json, .csv) -> Extracted as String.
        2. Native Assets (PDF, Image, Video, Audio) -> Uploaded as genai.types.File.
        3. Unsupported -> Raises ValueError (Safety Net).
        """
        logger.info(f"Parsing file: {file_path} with mime_type: {mime_type}")

        if not mime_type:
            mime_type = "application/octet-stream"

        mime_type = mime_type.lower()

        # Routing Logic: Text Assets
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

        elif mime_type.startswith("text/") or mime_type in TEXT_MIME_TYPES:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to read text file: {str(e)}")
                raise ValueError(f"Failed to read text file: {str(e)}")

        # Routing Logic: Native Assets (PDF/Image/Video/Audio)
        # Check against whitelist or broad categories supported by Gemini
        elif (mime_type in GEMINI_SUPPORTED_MIME_TYPES or
              mime_type.startswith("image/") or
              mime_type.startswith("video/") or
              mime_type.startswith("audio/")):
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

        else:
            # Safety Net: Unsupported MIME Type
            logger.error(f"Unsupported MIME type for Gemini upload: {mime_type}")
            raise ValueError(f"Unsupported MIME type for Gemini upload: {mime_type}")
