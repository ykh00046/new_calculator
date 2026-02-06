# Signature QA Tool - Quick Start Guide

## Launch the Application

### Method 1: From signature_qa_tool directory
```bash
cd C:\X\PythonProject\PythonProject3-program\v3\main\signature_qa_tool
python main.py
```

### Method 2: From main directory
```bash
cd C:\X\PythonProject\PythonProject3-program\v3\main
python -m signature_qa_tool.main
```

### Method 3: Using batch file
```bash
cd C:\X\PythonProject\PythonProject3-program\v3\main
run_signature_qa_tool.bat
```

## Quick Workflow

1. **Launch** the application using one of the methods above
2. **Select Worker** from the dropdown (김민호, 김민호3, or 문동식)
3. **Adjust Parameters** if needed (or leave as defaults)
4. **Set Number of Variations** (default: 6)
5. **Click "Generate Signatures"** and wait for generation to complete
6. **Review Results** - compare the generated variations in the grid
7. **Select Best Image** - click on your preferred variation
8. **Save** - click "Save Selected" for one image or "Save All" for all

## Generated Files

All generated images are saved to:
```
C:\X\PythonProject\PythonProject3-program\v3\main\signature_qa_tool\output\
```

Filename format: `{worker_name}_v{number}_{timestamp}.png`

Example: `김민호_v1_20251119_143025.png`

## Tips

- **Start with defaults**: Click "Reset Parameters" to restore default settings
- **One parameter at a time**: Adjust one parameter per batch for clearer comparison
- **Document successful combinations**: Take notes on parameter values that work well
- **Test all workers**: Different workers may need different parameter tuning

## Common Parameters to Adjust

| Parameter | Effect | Try Adjusting If |
|-----------|--------|------------------|
| Gaussian Blur Sigma | Edge smoothness | Signatures look too sharp or pixelated |
| Ink Alpha Factor | Signature opacity | Signatures too faint or too dark |
| Brightness Factor | Overall brightness | Signatures too light or too dark |
| Rotation Angle Range | Variation in rotation | Need more/less natural variation |

## Troubleshooting

**Application won't start**
- Make sure you're in the correct directory
- Check that PySide6 is installed: `pip install PySide6==5.15.11`

**No images generated**
- Verify signature files exist in `resources/signature/`
- Check that `resources/signature/image.jpeg` exists

**Images look wrong**
- Click "Reset Parameters" to restore defaults
- Check `config/config.json` for correct base values

## Next Steps

After finding optimal parameters:
1. Document the best parameter combinations
2. Update `config/config.json` with the optimal values
3. Test in the main application to ensure consistency

For detailed information, see [README.md](README.md)
