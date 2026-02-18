import google.generativeai as genai
from docx import Document
import os
import logging
from typing import Union, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CENTRALIZED ROUTING CONFIGURATION ---

# 1. Native Assets: Files that should be uploaded directly to Gemini API
#    (PDFs, Images, Videos, Audio)
GEMINI_NATIVE_MIME_TYPES = [
    # Document
    "application/pdf",
    # Images
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
    # Video
    "video/mp4",
    "video/mpeg",
    "video/mov",
    "video/avi",
    "video/x-flv",
    "video/mpg",
    "video/webm",
    "video/wmv",
    "video/3gpp",
    # Audio
    "audio/wav",
    "audio/mp3",
    "audio/aiff",
    "audio/aac",
    "audio/ogg",
    "audio/flac"
]

# 2. Text Assets: Files that must be parsed locally and injected as text
#    (Word, JSON, TXT, CSV, MD, etc.)
TEXT_PARSABLE_MIME_TYPES = [
    "application/json",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/csv",
    "text/markdown",
    "text/html",
    "text/xml",
    "text/rtf"
]

# Legacy Alias for Backward Compatibility (if any external imports exist)
GEMINI_SUPPORTED_MIME_TYPES = GEMINI_NATIVE_MIME_TYPES
TEXT_MIME_TYPES = TEXT_PARSABLE_MIME_TYPES

class FileParser:
    @staticmethod
    def parse_file(file_path: str, mime_type: str, display_name: Optional[str] = None) -> Union[str, genai.types.File]:
        """
        Parses a file based on its MIME type using strict routing logic.

        Routing Logic:
        1. Text Assets (defined in TEXT_PARSABLE_MIME_TYPES) -> Extracted as String.
        2. Native Assets (defined in GEMINI_NATIVE_MIME_TYPES) -> Uploaded as genai.types.File.
        3. Unsupported -> Raises ValueError (Deny-by-Default).
        """
        if not mime_type:
            mime_type = "application/octet-stream"

        mime_type = mime_type.lower().split(';')[0].strip() # Normalize: remove charset params
        logger.info(f"Parsing file: {file_path} with normalized mime_type: {mime_type}")

        # ROUTE 1: Text-Parsable Assets
        # Check specific types first, then generic text/ prefix
        if mime_type in TEXT_PARSABLE_MIME_TYPES or mime_type.startswith("text/"):

            # Sub-Route: Word Documents (.docx)
            if mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                try:
                    doc = Document(file_path)
                    full_text = []
                    for para in doc.paragraphs:
                        if para.text.strip():  # Only add non-empty paragraphs
                            full_text.append(para.text)
                    extracted = "\n".join(full_text)
                    logger.info(f"Successfully extracted text from DOCX: {len(extracted)} chars")
                    return extracted
                except Exception as e:
                    logger.error(f"Failed to parse DOCX: {str(e)}")
                    # Critical Failure: Do not fallback to Native Upload
                    raise ValueError(f"Failed to parse DOCX: {str(e)}")

            # Sub-Route: Plain Text / JSON / CSV / etc.
            else:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        logger.info(f"Successfully read text file: {len(content)} chars")
                        return content
                except Exception as e:
                    logger.error(f"Failed to read text file: {str(e)}")
                    raise ValueError(f"Failed to read text file: {str(e)}")

        # ROUTE 2: Native Assets (Upload to Gemini)
        elif mime_type in GEMINI_NATIVE_MIME_TYPES or mime_type.startswith("image/") or mime_type.startswith("video/") or mime_type.startswith("audio/") or mime_type == "application/pdf":
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

        # ROUTE 3: Deny-by-Default
        else:
            logger.error(f"Unsupported MIME type for Gemini upload: {mime_type}")
            raise ValueError(f"Unsupported MIME type: {mime_type}. File rejected.")
