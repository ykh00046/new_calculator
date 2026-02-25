# shared/path_setup.py
"""
Production Data Hub - Path Setup Utility

Provides a centralized way to set up import paths.
Instead of repeating sys.path.insert in every module, use this utility.

Usage:
    from shared.path_setup import ensure_import_path
    ensure_import_path(__file__)

Or for non-shared imports:
    from shared.path_setup import get_project_root
    root = get_project_root()
"""

from __future__ import annotations

import sys
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory (parent of shared/)."""
    # shared/path_setup.py -> shared/ -> project_root/
    return Path(__file__).resolve().parent.parent


def ensure_import_path(caller_file: str | Path) -> None:
    """
    Ensure the project root is in sys.path for imports.

    Args:
        caller_file: Pass __file__ from the calling module.

    Example:
        # At the top of api/main.py:
        from shared.path_setup import ensure_import_path
        ensure_import_path(__file__)
    """
    project_root = get_project_root()
    root_str = str(project_root)

    # Only add if not already present (avoid duplicates)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def setup_path_for_file(file_path: str | Path) -> Path:
    """
    Legacy compatibility: Add parent directory to sys.path.
    Returns the project root path.

    This matches the old pattern:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    Args:
        file_path: The __file__ of the calling module.

    Returns:
        The project root Path.
    """
    # For files in subdirectories (e.g., api/main.py), go up 2 levels
    # For files in root, just use the directory itself
    file_path = Path(file_path).resolve()
    parent = file_path.parent

    # Check if we're in a subdirectory (api/, dashboard/, tools/, etc.)
    if parent.name in ('api', 'dashboard', 'tools', 'tests') or (parent / 'shared').exists():
        project_root = parent
    else:
        project_root = parent.parent

    root_str = str(project_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    return project_root
