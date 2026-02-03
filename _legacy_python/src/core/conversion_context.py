from enum import Enum
from .pathfinder import Pathfinder

class FileType(Enum):
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    DOCUMENT = "document"
    EMAIL = "email"
    UNKNOWN = "unknown"

class ConversionContext:
    """
    Defines valid target formats for each source type.
    Now delegates to the Pathfinder (Omni-Matrix).
    """
    
    # Mapping Source Type -> List of Target Extensions
    # Kept for backward compatibility if needed, but get_formats_for_type should be dynamic now
    # Or strict mapping for categories?
    
    # Actually, we can just look up via a sample extension or the filetype enum?
    # FileType enum is broad. Pathfinder works on extensions.
    # The UI calls get_formats_for_type(ftype).
    # We need a representative extension for each FileType to query Pathfinder, 
    # OR we just query Pathfinder's categories directly.
    
    @staticmethod
    def get_formats_for_type(ftype: FileType) -> list[str]:
        # Basic mapping to representative sample for querying Pathfinder
        # This is a bit of a hack, but Pathfinder is extension-based.
        sample_ext = ""
        if ftype == FileType.VIDEO: sample_ext = ".mp4"
        elif ftype == FileType.AUDIO: sample_ext = ".mp3"
        elif ftype == FileType.IMAGE: sample_ext = ".jpg"
        elif ftype == FileType.DOCUMENT: sample_ext = ".docx"
        elif ftype == FileType.EMAIL: sample_ext = ".eml"
        else: return []
        
        return Pathfinder.get_supported_targets(sample_ext)
