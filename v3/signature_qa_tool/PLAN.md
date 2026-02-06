# Signature QA Tool Development Plan

## 1. Goal & Purpose

The primary goal of the Signature QA Tool is to efficiently generate, visualize, and evaluate a large number of synthesized signature images against a base document. This tool will help in:
- Identifying optimal `ImageProcessor` parameters for realism and visibility.
- Generating diverse sets of signatures for quality assurance.
- Providing a visual interface for quick comparison and selection of best-fit signatures.
- Ensuring consistency with the main application's image processing pipeline.

## 2. Core Requirements

1.  **Batch Signature Generation**: Ability to generate multiple variations of synthesized signatures using `models/image_processor.py` with configurable parameters.
2.  **Base Document Loading**: Load a reference base document image (e.g., `image.jpeg` from `resources/signature`).
3.  **Composite Image Creation**: Overlay generated signatures onto the base document at specified positions.
4.  **Visual Comparison Interface**: A simple GUI to display the composite images side-by-side or in a grid for easy comparison.
5.  **Parameter Control**: UI elements to adjust `ImageProcessor` parameters (e.g., blur, noise, contrast, brightness, randomization factors) and immediately see the effect on generated signatures.
6.  **Output Saving**: Option to save selected composite images or individual signature images for future use.
7.  **Consistency**: Leverage existing code from the main application (`models/image_processor.py`, `config/config_manager.py`, `utils/logger.py`) to ensure consistency.

## 3. Proposed Architecture & Components

The tool will be a standalone PySide6 application, following the structure of the main project.

### 3.1. `signature_qa_tool/main.py` (Application Entry Point)
- Initializes the PySide6 application.
- Creates and shows the main window.

### 3.2. `signature_qa_tool/ui/main_window.py` (Main GUI Window)
- **Layout**:
    - Left Panel: Parameter controls (spin boxes, sliders) for `ImageProcessor` settings.
    - Right Panel: Display area for composite images (e.g., a grid of generated signatures on the base document).
    - Bottom Panel: Action buttons (Generate, Save, Reset).
- **Controls**:
    - Spin boxes/sliders for `ImageProcessor` parameters (blur, noise, contrast, brightness, randomization factors).
    - Dropdown for selecting worker names (to generate specific signatures).
    - Button to trigger batch generation.
    - Button to save selected images.
- **Integration**:
    - Will use `config/config_manager.py` to load default parameters.
    - Will instantiate and interact with `SignatureGenerator` (see below).

### 3.3. `signature_qa_tool/processing/generator.py` (Signature Generation Logic)
- This class will encapsulate the logic for generating and compositing signatures.
- **Methods**:
    - `__init__(self, config_manager_instance)`: Takes the main application's `config` object.
    - `generate_composite_image(self, worker_name, params)`:
        - Loads the base document image.
        - Uses `models/image_processor.py` to create a synthesized signature.
        - Overlays the signature onto the base document.
        - Returns the composite PIL Image.
    - `generate_batch(self, worker_name, num_variations, params)`:
        - Calls `generate_composite_image` multiple times to create a batch of images.
        - Returns a list of composite PIL Images.

### 3.4. `signature_qa_tool/config/config.py` (Local Configuration)
- A simple local configuration file for the QA tool itself (e.g., default number of variations, output directory).
- Will also import and use the main application's `config/config_manager.py` for `ImageProcessor` settings.

## 4. Development Steps

1.  **Initial Setup**: Create `signature_qa_tool/main.py`, `signature_qa_tool/ui/main_window.py`, `signature_qa_tool/processing/generator.py`, `signature_qa_tool/config/config.py`.
2.  **Configuration Integration**: Ensure `config/config_manager.py` is accessible and its `signature` and `scan_effects` properties are used for default values.
3.  **`SignatureGenerator` Implementation**: Implement the core logic in `processing/generator.py` using `models/image_processor.py`.
4.  **GUI Implementation**: Design the `main_window.py` with parameter controls and an image display area.
5.  **Event Handling**: Connect UI controls to `SignatureGenerator` methods.
6.  **Testing**: Thoroughly test generation, display, and saving functionalities.

## 5. Discussion Points

-   **Parameter Granularity**: Which `ImageProcessor` parameters should be exposed in the GUI? (e.g., `gaussian_blur_sigma`, `pressure_noise_strength`, `mesh_warp` jitter, `randomization` ranges).
-   **Display Format**: How many composite images should be displayed at once? (e.g., 2x2, 3x3 grid).
-   **Comparison Features**: Should there be features like "select best" or "discard bad" directly in the UI?
-   **Output Naming**: How should saved images be named? (e.g., `worker_name_params_timestamp.png`).
-   **Integration with Main App**: How can this tool's findings (e.g., optimal parameter sets) be easily transferred back to the main `config.json`?

---
**작성일**: 2025-11-19
**작성자**: Gemini CLI
**버전**: 1.0
