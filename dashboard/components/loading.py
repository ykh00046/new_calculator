"""
U6: Loading State Display - Progress indicators and status display.

Provides loading state management with progress bars and
status indicators for data operations.
"""

import streamlit as st
from datetime import datetime
from typing import Optional


class LoadingContext:
    """
    Context manager for loading state with progress bar.

    Usage:
        with show_loading_status("Loading data...") as loader:
            loader.update(0.5, "Halfway there...")
            # do work
            loader.update(1.0, "Complete!")
    """

    def __init__(self, message: str = "Loading..."):
        """
        Initialize loading context.

        Args:
            message: Initial loading message to display.
        """
        self.msg = message
        self.placeholder: Optional[st.empty] = None
        self.progress_bar = None

    def __enter__(self) -> "LoadingContext":
        """Enter context and create progress bar."""
        self.placeholder = st.empty()
        self.progress_bar = self.placeholder.progress(0, text=self.msg)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context and clean up progress bar."""
        if self.progress_bar is not None:
            self.progress_bar.empty()

    def update(self, progress: float, message: Optional[str] = None) -> None:
        """
        Update progress bar.

        Args:
            progress: Progress value from 0.0 to 1.0.
            message: Optional new message to display.
        """
        if self.progress_bar is not None:
            msg = message or self.msg
            self.progress_bar.progress(int(progress * 100), text=msg)


def show_loading_status(message: str = "Loading data...") -> LoadingContext:
    """
    Create a loading state context manager.

    Args:
        message: Loading message to display.

    Returns:
        LoadingContext instance for use with 'with' statement.

    Example:
        with show_loading_status("Fetching records...") as loader:
            # Load data
            df = load_data()
            loader.update(0.5, "Processing...")
            # Process data
            process(df)
    """
    return LoadingContext(message)


def render_last_update() -> None:
    """
    Render last update timestamp.

    Displays the current timestamp indicating when data was last refreshed.
    """
    st.caption(f"Last updated: {datetime.now():%Y-%m-%d %H:%M:%S}")


def render_cache_status(cache_hit: bool) -> None:
    """
    Render cache hit/miss indicator.

    Args:
        cache_hit: True if data came from cache, False if from database.

    Displays a small status indicator showing whether data was loaded
    from cache or fetched from the database.
    """
    if cache_hit:
        st.success("Loaded from cache", icon=":")
    else:
        st.info("Fetched from database", icon=":")
