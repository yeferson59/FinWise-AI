"""
OCR Cache System
Implements caching for OCR results to avoid reprocessing identical images.
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Any


# Cache directory
CACHE_DIR = Path("./cache/ocr")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_file_hash(filepath: str) -> str:
    """
    Calculate SHA256 hash of a file.
    
    Args:
        filepath: Path to the file
        
    Returns:
        Hexadecimal hash string
    """
    try:
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        # If hashing fails, return a timestamp-based fallback
        print(f"Warning: Failed to hash file {filepath}: {e}")
        return f"fallback_{int(time.time() * 1000)}"


def get_cache_key(filepath: str, config_dict: dict[str, Any]) -> str:
    """
    Generate cache key based on file content and configuration.
    
    Args:
        filepath: Path to the file
        config_dict: Configuration dictionary (OCR settings, document type, etc.)
        
    Returns:
        Cache key string
    """
    file_hash = get_file_hash(filepath)
    
    # Create deterministic string from config
    config_str = json.dumps(config_dict, sort_keys=True, default=str)
    config_hash = hashlib.md5(config_str.encode()).hexdigest()[:8]
    
    return f"{file_hash[:16]}_{config_hash}"


def get_cached_result(filepath: str, config: dict[str, Any]) -> dict[str, Any] | None:
    """
    Retrieve cached OCR result if it exists and is still valid.
    
    Args:
        filepath: Path to the file
        config: Configuration dictionary
        
    Returns:
        Cached result dictionary or None if not found/invalid
    """
    try:
        cache_key = get_cache_key(filepath, config)
        cache_file = CACHE_DIR / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        # Check if cache is not too old (default: 7 days)
        max_age_seconds = 7 * 24 * 60 * 60
        file_age = time.time() - cache_file.stat().st_mtime
        
        if file_age > max_age_seconds:
            # Cache too old, delete it
            cache_file.unlink()
            return None
        
        # Load and return cached result
        with open(cache_file, 'r', encoding='utf-8') as f:
            cached_data = json.load(f)
            
        # Add cache hit metadata
        cached_data['_cache_hit'] = True
        cached_data['_cache_age_seconds'] = int(file_age)
        
        return cached_data
        
    except Exception as e:
        print(f"Warning: Failed to retrieve cached result: {e}")
        return None


def cache_result(filepath: str, config: dict[str, Any], result: dict[str, Any]) -> bool:
    """
    Save OCR result to cache.
    
    Args:
        filepath: Path to the file
        config: Configuration dictionary
        result: Result dictionary to cache
        
    Returns:
        True if cached successfully, False otherwise
    """
    try:
        cache_key = get_cache_key(filepath, config)
        cache_file = CACHE_DIR / f"{cache_key}.json"
        
        # Add metadata
        cache_data = result.copy()
        cache_data['_cached_at'] = time.time()
        cache_data['_cache_key'] = cache_key
        
        # Write to temporary file first, then rename (atomic operation)
        temp_file = cache_file.with_suffix('.tmp')
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        
        temp_file.rename(cache_file)
        return True
        
    except Exception as e:
        print(f"Warning: Failed to cache result: {e}")
        return False


def clear_cache(max_age_days: int = 7) -> tuple[int, int]:
    """
    Clear old cache files.
    
    Args:
        max_age_days: Maximum age in days for cache files
        
    Returns:
        Tuple of (files_removed, errors)
    """
    try:
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        files_removed = 0
        errors = 0
        
        for cache_file in CACHE_DIR.glob("*.json"):
            try:
                file_age = current_time - cache_file.stat().st_mtime
                if file_age > max_age_seconds:
                    cache_file.unlink()
                    files_removed += 1
            except Exception as e:
                print(f"Error removing cache file {cache_file}: {e}")
                errors += 1
        
        return files_removed, errors
        
    except Exception as e:
        print(f"Error clearing cache: {e}")
        return 0, 1


def get_cache_stats() -> dict[str, Any]:
    """
    Get statistics about the cache.
    
    Returns:
        Dictionary with cache statistics
    """
    try:
        cache_files = list(CACHE_DIR.glob("*.json"))
        total_files = len(cache_files)
        
        if total_files == 0:
            return {
                'total_files': 0,
                'total_size_mb': 0,
                'oldest_file_age_days': 0,
                'newest_file_age_days': 0
            }
        
        total_size = sum(f.stat().st_size for f in cache_files)
        current_time = time.time()
        
        ages = [(current_time - f.stat().st_mtime) / 86400 for f in cache_files]
        
        return {
            'total_files': total_files,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'oldest_file_age_days': round(max(ages), 1) if ages else 0,
            'newest_file_age_days': round(min(ages), 1) if ages else 0
        }
        
    except Exception as e:
        print(f"Error getting cache stats: {e}")
        return {'error': str(e)}


def invalidate_cache_for_file(filepath: str) -> int:
    """
    Invalidate all cached results for a specific file.
    
    Args:
        filepath: Path to the file
        
    Returns:
        Number of cache entries removed
    """
    try:
        file_hash = get_file_hash(filepath)[:16]
        pattern = f"{file_hash}_*.json"
        
        removed = 0
        for cache_file in CACHE_DIR.glob(pattern):
            cache_file.unlink()
            removed += 1
        
        return removed
        
    except Exception as e:
        print(f"Error invalidating cache: {e}")
        return 0
