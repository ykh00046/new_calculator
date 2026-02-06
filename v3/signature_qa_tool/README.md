# Signature QA Tool

A PySide6 application for generating, visualizing, and evaluating synthesized signature images to optimize ImageProcessor parameters.

## Purpose

The Signature QA Tool helps in:
- **Parameter Optimization**: Fine-tune `ImageProcessor` parameters for optimal signature realism and visibility
- **Batch Generation**: Generate multiple signature variations simultaneously for comparison
- **Visual Evaluation**: Compare signatures side-by-side in a grid layout
- **Quality Assurance**: Ensure consistent signature quality before production use

## Features

### 1. Worker Selection
- Select from configured workers (김민호, 김민호3, 문동식)
- Generates signatures specific to each worker

### 2. Adjustable Parameters
- **Gaussian Blur Sigma**: Control edge smoothness (0.0 - 5.0)
- **Pressure Noise Strength**: Simulate pen pressure variations (0.0 - 0.5)
- **Ink Alpha Factor**: Control signature opacity (1.0 - 3.0)
- **Brightness Factor**: Adjust signature brightness (0.5 - 2.0)
- **Final Contrast Factor**: Control overall image contrast (0.5 - 2.0)
- **Rotation Angle Range**: Randomization range for signature rotation (0 - 30°)
- **Offset X/Y Range**: Position randomization (0 - 20 pixels)
- **Scale Min/Max**: Size variation range (0.5 - 1.0)
- **Mesh Warp Jitter**: Geometric distortion amount (0 - 10)

### 3. Batch Generation
- Generate 1-12 variations at once
- Default: 6 variations (2 rows × 3 columns)
- Progress bar shows generation status

### 4. Image Display
- Grid layout for easy comparison
- Click to select individual images
- Visual feedback on selection (green border)

### 5. Save Options
- **Save Selected**: Save a single chosen variation
- **Save All**: Save all generated variations
- Files saved to: `signature_qa_tool/output/`
- Naming format: `{worker_name}_v{number}_{timestamp}.png`

## Usage

### Running the Application

#### Option 1: From Main Directory (Recommended)
```bash
cd C:\X\PythonProject\PythonProject3-program\v3\main
python -m signature_qa_tool.main
```

#### Option 2: From signature_qa_tool Directory
```bash
cd C:\X\PythonProject\PythonProject3-program\v3\main\signature_qa_tool
python main.py
```

#### Option 3: Batch File
```bash
# From main directory:
run_signature_qa_tool.bat
```

**Note**: The application automatically adjusts paths regardless of which directory you run it from.

### Workflow

1. **Select Worker**: Choose the worker from the dropdown
2. **Adjust Parameters**: Fine-tune ImageProcessor settings
3. **Set Variations**: Choose how many variations to generate (1-12)
4. **Generate**: Click "Generate Signatures" button
5. **Review**: Compare the generated variations in the grid
6. **Select**: Click on the best variation (optional)
7. **Save**:
   - Click "Save Selected" to save one image
   - Click "Save All" to save all variations
8. **Iterate**: Adjust parameters and regenerate for comparison

### Finding Optimal Parameters

1. Start with default parameters (click "Reset Parameters")
2. Generate a batch to see baseline quality
3. Adjust one parameter at a time
4. Compare results to identify improvements
5. Document successful parameter combinations
6. Transfer optimal settings to `config/config.json`

## Architecture

### Directory Structure
```
signature_qa_tool/
├── main.py                  # Application entry point
├── config/
│   ├── __init__.py
│   └── config.py           # Configuration management
├── processing/
│   ├── __init__.py
│   └── generator.py        # Signature generation logic
├── ui/
│   ├── __init__.py
│   └── main_window.py      # Main GUI window
├── output/                 # Generated images (created automatically)
├── PLAN.md                # Development plan
└── README.md              # This file
```

### Integration with Main Application

The tool leverages existing components:
- **`models/image_processor.py`**: Core signature synthesis logic
- **`config/config_manager.py`**: Configuration loading
- **`config/config.json`**: Default parameter values
- **`resources/signature/`**: Signature images and base document

## Parameter Reference

### Recommended Ranges

| Parameter | Recommended Range | Purpose |
|-----------|------------------|---------|
| Gaussian Blur Sigma | 0.5 - 1.0 | Smooths edges, prevents jaggedness |
| Pressure Noise | 0.0 - 0.1 | Adds realistic pen pressure variation |
| Ink Alpha Factor | 1.3 - 1.8 | Controls signature opacity |
| Brightness Factor | 1.1 - 1.4 | Lightens/darkens signature |
| Final Contrast | 1.2 - 1.6 | Overall image contrast |
| Rotation Angle | 4 - 12 | Natural handwriting variation |
| Offset X | 0 - 3 | Horizontal position variation |
| Offset Y | 0 - 5 | Vertical position variation |
| Scale Min/Max | 0.90 - 0.98 | Size consistency |

### Current Defaults (from config.json)

```json
{
  "gaussian_blur_sigma": 0.7,
  "pressure_noise_strength": 0.0,
  "ink_alpha_factor": 1.5,
  "signature_brightness_factor": 1.25,
  "final_contrast_factor": 1.4,
  "randomization": {
    "rotation_angle": 8,
    "offset_x": 1,
    "offset_y": 2,
    "scale_min": 0.95,
    "scale_max": 0.98
  }
}
```

## Tips for Best Results

1. **Start Conservative**: Begin with small parameter changes
2. **One at a Time**: Adjust one parameter per batch for clear comparisons
3. **Document Results**: Take notes on successful combinations
4. **Test Multiple Workers**: Parameters may need tuning per worker
5. **Save Comparisons**: Use "Save All" to keep reference sets
6. **Consider Context**: Signature visibility depends on base document

## Troubleshooting

### Application Won't Start
- Ensure PySide6 is installed: `pip install PySide6==5.15.11`
- Check Python path includes main application directory
- Verify `resources/signature/image.jpeg` exists

### No Images Generated
- Check worker signature files exist in `resources/signature/`
- Verify base document exists: `resources/signature/image.jpeg`
- Check console output for error messages

### Images Look Incorrect
- Reset parameters to defaults
- Verify `config/config.json` is valid JSON
- Check that signature files are valid PNG images

## Future Enhancements

Potential improvements:
- Side-by-side comparison mode
- Parameter preset saving/loading
- Automatic quality scoring
- Export parameter sets to config.json
- Batch processing for multiple workers
- A/B testing interface

---

**Version**: 1.0.0
**Created**: 2025-11-19
**Dependencies**: PySide6, PIL, numpy
