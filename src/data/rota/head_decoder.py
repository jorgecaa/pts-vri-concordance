"""
Header decoder integration module for Tipitaka PTS backend.

This module provides a clean interface for decoding garbled HEAD fields
from the tipitaka.sqlite database. It wraps the HeaderDecoderWithTable
class and provides caching for performance.
"""

import sys
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

# Add parent directory to path to import decoder
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from header_decoder_with_table import HeaderDecoderWithTable


class HeadDecoder:
    """
    Decoder for garbled HEAD fields from Tipitaka PTS database.

    This class provides a simple interface to decode the proprietary-encoded
    HEAD fields back to readable Pali text with diacritics.

    Usage:
        decoder = HeadDecoder()
        decoded_text = decoder.decode(head_field_bytes)
    """

    def __init__(self, use_cache: bool = True):
        """
        Initialize the decoder.

        Args:
            use_cache: Whether to cache decoded results for performance
        """
        self.use_cache = use_cache
        if use_cache:
            # Wrap the decode method with LRU cache
            self._decode_cached = lru_cache(maxsize=10000)(
                HeaderDecoderWithTable.decode_header
            )

    def decode(self, head_value: str) -> str:
        """
        Decode a HEAD field value.

        The HEAD field from the database is already a string (not raw bytes),
        so this method converts it to bytes and decodes.

        Args:
            head_value: The HEAD field value from the database (string)

        Returns:
            Decoded Pali text with diacritics
        """
        if not head_value:
            return ""

        # Convert string to UTF-8 bytes (it's already decoded from database)
        head_bytes = head_value.encode("utf-8")

        # Decode using cached or uncached method
        if self.use_cache:
            return self._decode_cached(head_bytes)
        else:
            return HeaderDecoderWithTable.decode_header(head_bytes)

    def decode_bytes(self, head_bytes: bytes) -> str:
        """
        Decode HEAD field from raw bytes.

        Args:
            head_bytes: Raw UTF-8 bytes of the HEAD field

        Returns:
            Decoded Pali text with diacritics
        """
        if not head_bytes:
            return ""

        if self.use_cache:
            return self._decode_cached(head_bytes)
        else:
            return HeaderDecoderWithTable.decode_header(head_bytes)

    def get_decoder_stats(self) -> Dict:
        """
        Get statistics about the decoder.

        Returns:
            Dictionary with decoder information
        """
        stats = {
            "mappings_count": len(HeaderDecoderWithTable.LATIN1_TO_ORIGINAL),
            "special_chars_count": len(HeaderDecoderWithTable.ORIGINAL_TO_UNICODE),
        }

        if self.use_cache and hasattr(self, "_decode_cached"):
            cache_info = self._decode_cached.cache_info()
            stats["cache_hits"] = cache_info.hits
            stats["cache_misses"] = cache_info.misses
            stats["cache_size"] = cache_info.currsize
            stats["cache_maxsize"] = cache_info.maxsize

        return stats

    def clear_cache(self) -> None:
        """Clear the decode cache if caching is enabled."""
        if self.use_cache and hasattr(self, "_decode_cached"):
            self._decode_cached.cache_clear()


# Module-level singleton for easy access
_decoder_instance: Optional[HeadDecoder] = None


def get_decoder(use_cache: bool = True) -> HeadDecoder:
    """
    Get the global decoder instance.

    Args:
        use_cache: Whether to use caching (only applies on first call)

    Returns:
        HeadDecoder instance
    """
    global _decoder_instance
    if _decoder_instance is None:
        _decoder_instance = HeadDecoder(use_cache=use_cache)
    return _decoder_instance


def decode_head(head_value: str) -> str:
    """
    Convenience function to decode a HEAD field.

    This is the simplest way to decode HEAD fields:

        from src.data.rota.head_decoder import decode_head
        decoded = decode_head(head_field_value)

    Args:
        head_value: The HEAD field value from the database

    Returns:
        Decoded Pali text with diacritics
    """
    return get_decoder().decode(head_value)


def decode_head_bytes(head_bytes: bytes) -> str:
    """
    Convenience function to decode HEAD field from raw bytes.

    Args:
        head_bytes: Raw UTF-8 bytes of the HEAD field

    Returns:
        Decoded Pali text with diacritics
    """
    return get_decoder().decode_bytes(head_bytes)
