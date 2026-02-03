from ..utils.logger import logger

class Pathfinder:
    """
    The Omni-Matrix Graph Engine.
    Calculates the shortest conversion path between any two file formats.
    """

    # ==========================================
    # MASTER FILE SUPPORT MATRIX (Source of Truth)
    # ==========================================

    # 1. VIDEO FORMATS (Engine: FFmpeg)
    VIDEO_FORMATS = [
        "mp4", "mkv", "avi", "mov", "wmv", "flv", "webm", "vob", "ogv", 
        "3gp", "m4v", "mpg", "mpeg", "m2ts", "asf", "divx", "rmvb"
    ]

    # 2. AUDIO FORMATS (Engine: FFmpeg)
    AUDIO_FORMATS = [
        "mp3", "wav", "aac", "flac", "ogg", "m4a", "opus", "wma", 
        "aiff", "alac", "pcm", "aif", "amr"
    ]

    # 3. IMAGE FORMATS (Engine: ImageMagick + Pillow)
    IMAGE_FORMATS = [
        "jpg", "jpeg", "png", "webp", "tiff", "bmp", "ico", "gif", 
        "svg", "heic", "heif", "avif", "raw", "cr2", "nef", "arw", 
        "psd", "ai", "eps", "tga", "dds"
    ]

    # 4. DOCUMENT FORMATS (Engine: LibreOffice Headless / Pandoc)
    DOC_FORMATS = [
        "docx", "doc", "odt", "rtf", "txt", "pdf", "html", "htm", 
        "pptx", "ppt", "odp", "xlsx", "xls", "ods", "csv", "xml"
    ]

    # 5. EBOOK FORMATS (Engine: Pandoc)
    EBOOK_FORMATS = [
        "epub", "mobi", "azw3", "fb2", "cbz", "lit", "lrf"
    ]

    # 6. ARCHIVE FORMATS (Engine: Python zipfile/tarfile)
    ARCHIVE_FORMATS = [
        "zip", "rar", "7z", "tar", "gz", "bz2", "iso"
    ]
    
    # Categories for Logic
    CATS = {
        'video': VIDEO_FORMATS,
        'audio': AUDIO_FORMATS,
        'image': IMAGE_FORMATS,
        'doc': DOC_FORMATS,
        'ebook': EBOOK_FORMATS,
        'archive': ARCHIVE_FORMATS
    }

    # Bridges define how to jump between categories
    # Key: (SourceCat, TargetCat) -> Intermediate Format
    BRIDGES = {
        ('video', 'doc'): 'gif', # Video -> GIF -> PDF -> DOCX
        ('video', 'image'): 'jpg', # Video -> JPG (Sequence)
        ('audio', 'video'): 'mp4', # Audio -> MP4 (Visualizer)
        ('image', 'doc'): 'pdf', # Image -> PDF -> DOCX
        ('doc', 'image'): 'pdf', # DOCX -> PDF -> JPG
        ('ebook', 'audio'): 'txt', # EPUB -> TXT -> MP3 (TTS)
        ('html', 'doc'): 'pdf' # HTML -> PDF -> DOCX
    }

    @staticmethod
    def get_category(fmt):
        fmt = fmt.lower().strip('.')
        for cat, opts in Pathfinder.CATS.items():
            if fmt in opts: return cat
        return None

    @staticmethod
    def find_path(source_fmt, target_fmt):
        """
        Returns a list of steps: [{'from': 'mp4', 'to': 'gif', 'engine': 'ffmpeg'}, ...]
        """
        source = source_fmt.lower().strip('.')
        target = target_fmt.lower().strip('.')
        
        cat_s = Pathfinder.get_category(source)
        cat_t = Pathfinder.get_category(target)
        
        if not cat_s: return None # Unknown source
        
        # Scenario 1: Same Category (Direct)
        if cat_s == cat_t:
            return [{
                'src': source,
                'tgt': target,
                'engine': Pathfinder._get_engine_for_cat(cat_s)
            }]
            
        # Scenario 2: Different Category (Bridged)
        # Check bridges
        bridge_key = (cat_s, cat_t)
        if bridge_key in Pathfinder.BRIDGES:
            bridge_fmt = Pathfinder.BRIDGES[bridge_key]
            
            # Step 1: Source -> Bridge
            step1 = {
                'src': source,
                'tgt': bridge_fmt,
                'engine': Pathfinder._get_engine_for_cat(cat_s) # Use source engine to get to bridge? 
                # e.g. Video -> GIF (FFmpeg)
            }
            
            # Step 2: Bridge -> Target
            # Recursively find path for bridge -> target?
            # Or just assume bridge connects?
            # e.g. GIF (Image) -> PDF (Doc) is bridged again?
            # Yes, GIF is Image. PDF is Doc. Bridge is ('image', 'doc') -> 'pdf'
            
            # Let's simple-chain for now (2 steps max for MVP, or 3)
            # Video -> GIF (Image)
            # GIF (Image) -> PDF (Doc) -> DOCX
            
            # This requires a real graph search.
            # Building simple Adjacency List for categories
            # Video -> Image (via gif/jpg)
            # Image -> Doc (via pdf)
            # Doc -> Image (via pdf)
            
            # Implementing BFS on Categories?
            # Nodes: Categories. Edges: Bridges.
            
            path_cat = Pathfinder._bfs_categories(cat_s, cat_t)
            if not path_cat: return None
            
            # Now build file steps
            # path_cat = ['video', 'image', 'doc']
            generated_steps = []
            
            current_fmt = source
            
            for i in range(len(path_cat) - 1):
                c_current = path_cat[i]
                c_next = path_cat[i+1]
                
                # Find bridge format
                if (c_current, c_next) in Pathfinder.BRIDGES:
                    bridge = Pathfinder.BRIDGES[(c_current, c_next)]
                    
                    # Add Step
                    generated_steps.append({
                        'src': current_fmt,
                        'tgt': bridge,
                        'engine': Pathfinder._get_engine_for_cat(c_current)
                    })
                    current_fmt = bridge
                else: 
                     # Implicit bridge? Or error?
                     return None
            
            # Final Step: bridge -> target
            # current_fmt is now in c_next category (or close to it)
            # Wait, if bridge was 'pdf' (Doc) and target is 'docx' (Doc), we need one last step?
            # Yes.
            
            if current_fmt != target:
                generated_steps.append({
                    'src': current_fmt,
                    'tgt': target,
                    'engine': Pathfinder._get_engine_for_cat(cat_t)
                })
                
            return generated_steps

        return None

    @staticmethod
    def _get_engine_for_cat(cat):
        if cat in ['video', 'audio']: return 'ffmpeg'
        if cat == 'image': return 'image_engine' # Pillow
        if cat == 'doc': return 'doc_engine'
        if cat == 'ebook': return 'doc_engine' # Pandoc
        return 'unknown'

    @staticmethod
    def get_supported_targets(source_fmt):
        """
        Returns a sorted list of all valid target formats for a given source.
        """
        source = source_fmt.lower().strip('.')
        cat_s = Pathfinder.get_category(source)
        if not cat_s: return []
        
        # Simple BFS reachability
        reachable_cats = set()
        queue = [cat_s]
        
        # Graph logic repeated for reachability (could be optimized)
        graph = {
            'video': ['image', 'doc', 'audio'], 
            'audio': ['video'], 
            'image': ['doc', 'video'], 
            'doc': ['image', 'ebook', 'pdf'], # pdf special handling?
            'ebook': ['doc', 'audio'],
            'archive': [] # Archive currently isolated or internal
        }
        # Explicit graph correction to match BRIDGES keys
        # BRIDGES = { ('video', 'doc'), ('video', 'image'), ... }
        # Re-build adjacency from BRIDGES
        adj = {}
        for (src, tgt) in Pathfinder.BRIDGES.keys():
            if src not in adj: adj[src] = []
            adj[src].append(tgt)
        # Add self-loops (Category -> Same Category is always possible)
        for c in Pathfinder.CATS:
            if c not in adj: adj[c] = []
            adj[c].append(c)
            
        # Run BFS
        visited_cats = {cat_s}
        q = [cat_s]
        
        while q:
            curr = q.pop(0)
            # Add neighbors from Bridge
            neighbors = adj.get(curr, [])
            # Also add neighbors from hardcoded graph? No, BRIDGES is source of truth?
            # Actually, BRIDGES defines cross-cat. Inside cat is always true.
            
            for n in neighbors:
                if n not in visited_cats:
                    visited_cats.add(n)
                    q.append(n)
        
        # Collect formats from all visited categories
        targets = set()
        for cat in visited_cats:
            for fmt in Pathfinder.CATS.get(cat, []):
                targets.add("." + fmt)
                
        # Always include same-category formats (just in case bridge logic missed self)
        for fmt in Pathfinder.CATS.get(cat_s, []):
             targets.add("." + fmt)
             
        # Remove source itself if desired, or keep (converting mp4 to mp4 is valid re-encode)
        
        return sorted(list(targets))

    @staticmethod
    def _bfs_categories(start, end):
        # Graph of Categories
        graph = {
            'video': ['image', 'doc'], # via gif/jpg
            'audio': ['video'], # via mp4
            'image': ['doc', 'video'], # via pdf / sequence
            'doc': ['image', 'ebook'], # via pdf / pandoc
            'ebook': ['doc', 'audio'] # via pandoc / tts
        }
        
        queue = [[start]]
        seen = {start}
        
        while queue:
            path = queue.pop(0)
            node = path[-1]
            if node == end: return path
            
            for neighbor in graph.get(node, []):
                if neighbor not in seen:
                    seen.add(neighbor)
                    new_path = list(path)
                    new_path.append(neighbor)
                    queue.append(new_path)
        return None
