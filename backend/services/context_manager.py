"""
Context manager for maintaining rolling transcript history.
Keeps track of the last 30 seconds of transcripts.
"""
import logging
from typing import List
from datetime import datetime, timedelta
from collections import deque

logger = logging.getLogger(__name__)

# Configuration for context window
CONTEXT_WINDOW_SECONDS = 30
MAX_CONTEXT_ITEMS = 10  # Maximum number of transcript chunks to keep


class TranscriptContext:
    """Manages a rolling window of transcripts for context."""
    
    def __init__(self, window_seconds: int = CONTEXT_WINDOW_SECONDS):
        """
        Initialize the transcript context manager.
        
        Args:
            window_seconds: Time window to maintain context for
        """
        self.window_seconds = window_seconds
        self.transcripts: deque = deque(maxlen=MAX_CONTEXT_ITEMS)
        self.timestamps: deque = deque(maxlen=MAX_CONTEXT_ITEMS)
        
    def add_transcript(self, text: str) -> None:
        """
        Add a new transcript to the context.
        
        Args:
            text: Transcript text to add
        """
        if text.strip():  # Only add non-empty transcripts
            self.transcripts.append(text)
            self.timestamps.append(datetime.now())
            logger.debug(f"Added transcript: {text[:30]}...")
    
    def get_context(self) -> str:
        """
        Get the full context string from all stored transcripts.
        
        Returns:
            Combined transcripts within the time window
        """
        now = datetime.now()
        cutoff_time = now - timedelta(seconds=self.window_seconds)
        
        context_parts = []
        for transcript, timestamp in zip(self.transcripts, self.timestamps):
            if timestamp >= cutoff_time:
                context_parts.append(transcript)
        
        return " ".join(context_parts)
    
    def get_all_transcripts(self) -> List[str]:
        """
        Get all transcripts in the context.
        
        Returns:
            List of all transcripts
        """
        return list(self.transcripts)
    
    def clear(self) -> None:
        """Clear all stored transcripts."""
        self.transcripts.clear()
        self.timestamps.clear()
        logger.debug("Context cleared")
    
    def __len__(self) -> int:
        """Return number of transcripts in context."""
        return len(self.transcripts)
    
    def __repr__(self) -> str:
        """String representation of context."""
        return f"TranscriptContext(items={len(self.transcripts)}, window={self.window_seconds}s)"


# Global instance for the main application
_context_instance: TranscriptContext = None


def get_context_manager() -> TranscriptContext:
    """Get or create the global context manager."""
    global _context_instance
    if _context_instance is None:
        _context_instance = TranscriptContext()
    return _context_instance


def reset_context_manager() -> None:
    """Reset the context manager (useful for testing)."""
    global _context_instance
    if _context_instance:
        _context_instance.clear()
    _context_instance = None
