"""
Signature QA Tool - Main Entry Point

A PySide6 application for generating, visualizing, and evaluating synthesized
signature images to optimize ImageProcessor parameters.

Usage:
    From main app directory:
        python -m signature_qa_tool.main

    IMPORTANT: This tool must be run from the main application directory
    (C:\\X\\PythonProject\\PythonProject3-program\\v3\\main), not from
    within the signature_qa_tool directory.
"""
import sys
import os

# Determine the correct base path
current_dir = os.path.dirname(os.path.abspath(__file__))

# Check if we're in the signature_qa_tool directory or main directory
if os.path.basename(current_dir) == "signature_qa_tool":
    # We're inside signature_qa_tool, need to go up one level
    main_dir = os.path.dirname(current_dir)
else:
    # We're likely in main directory already
    main_dir = current_dir

# IMPORTANT: Change working directory and prioritize main app imports
os.chdir(main_dir)

# Remove signature_qa_tool from path if it's there (to avoid conflicts)
sys.path = [p for p in sys.path if 'signature_qa_tool' not in p]

# Add main directory at the beginning
if main_dir not in sys.path:
    sys.path.insert(0, main_dir)

from PySide6.QtWidgets import QApplication
from signature_qa_tool.config.config import qa_config
from signature_qa_tool.ui.main_window import MainWindow


def main():
    """Main entry point for the Signature QA Tool."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Create and show main window
    window = MainWindow(qa_config)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
