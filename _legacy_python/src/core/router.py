import magic
import os
from .conversion_context import FileType
from ..utils.logger import logger

class MagicRouter:
    """
    Detects file types using magic bytes (MIME type) and routes them to the appropriate engine category.
    """
    
    MIME_MAPPING = {
        'video': FileType.VIDEO,
        'audio': FileType.AUDIO,
        'image': FileType.IMAGE,
        'application/pdf': FileType.DOCUMENT,
        'text/plain': FileType.DOCUMENT,
        'application/vnd.openxmlformats-officedocument': FileType.DOCUMENT,
        'application/msword': FileType.DOCUMENT,
        'application/vnd.oasis.opendocument': FileType.DOCUMENT, # ODT
        'application/rtf': FileType.DOCUMENT,
        'application/epub+zip': FileType.DOCUMENT,
        # Email
        'message/rfc822': FileType.EMAIL,
        'application/vnd.ms-outlook': FileType.EMAIL
    }

    def __init__(self):
        # python-magic-bin should handle this automatically on Windows
        pass

    def detect_file_type(self, file_path: str) -> FileType:
        """
        Identify the file type based on content, not extension.
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return FileType.UNKNOWN

        try:
            # from_file reads the header bytes
            mime_type = magic.from_file(file_path, mime=True)
            logger.debug(f"Detected MIME for {os.path.basename(file_path)}: {mime_type}")
            
            # Simple prefix matching for main categories
            if mime_type.startswith('video/'):
                return FileType.VIDEO
            if mime_type.startswith('audio/'):
                return FileType.AUDIO
            if mime_type.startswith('image/'):
                return FileType.IMAGE
                
            # Exact matching for documents
            for key, msg_type in self.MIME_MAPPING.items():
                if mime_type.startswith(key):
                    return msg_type
            
            return FileType.UNKNOWN

        except Exception as e:
            logger.error(f"Error identifying file {file_path}: {e}")
            return FileType.UNKNOWN
