"""
Local configuration for the Signature QA Tool.

This module provides tool-specific settings while leveraging the main
application's config_manager for ImageProcessor parameters.
"""
import os
import sys
import importlib.util


def _get_main_app_path():
    """Get the path to the main application root."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # signature_qa_tool/config -> signature_qa_tool -> main
    return os.path.dirname(os.path.dirname(current_dir))


def _load_main_config():
    """Load the main application's config using importlib to avoid naming conflicts."""
    main_app_path = _get_main_app_path()
    config_manager_path = os.path.join(main_app_path, "config", "config_manager.py")

    if not os.path.exists(config_manager_path):
        raise ImportError(
            f"Cannot find config_manager.py at {config_manager_path}. "
            f"Make sure you're running from the correct directory."
        )

    # Load the module using importlib
    spec = importlib.util.spec_from_file_location("main_config_manager", config_manager_path)
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)

    return config_module.config


# Add main app to path for other imports (like ImageProcessor)
_main_app_path = _get_main_app_path()
if _main_app_path not in sys.path:
    sys.path.insert(0, _main_app_path)

# Load main app's config
main_config = _load_main_config()


class QAToolConfig:
    """Configuration for the Signature QA Tool."""

    def __init__(self):
        self.main_app_path = _main_app_path
        self.main_config = main_config

        # Tool-specific settings
        self.default_num_variations = 6
        self.grid_columns = 3
        self.grid_rows = 2
        self.output_directory = os.path.join(self.main_app_path, "signature_qa_tool", "output")
        self.base_document_path = os.path.join(
            self.main_app_path, "resources", "signature", "image.jpeg"
        )

        # Ensure output directory exists
        os.makedirs(self.output_directory, exist_ok=True)

    def get_signature_config(self):
        """Get signature configuration from main app."""
        return self.main_config.get("signature", {})

    def get_workers(self):
        """Get worker names from main app."""
        return self.main_config.workers

    def get_resources_path(self):
        """Get the resources path for signature images."""
        return os.path.join(self.main_app_path, "resources", "signature")


# Global instance
qa_config = QAToolConfig()
