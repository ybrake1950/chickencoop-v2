# Phase 1 Implementation Stubs

This directory contains implementation stubs for Phase 1 modules. These are **reference implementations** to help you understand what each module should do.

## How to Use

1. Copy the stub file to the appropriate location in `src/`
2. Run the corresponding test file
3. Adjust the implementation until all tests pass

## Files

| Stub File | Copy To | Test File |
|-----------|---------|-----------|
| `config_validation.py` | `src/config/validation.py` | `test_config_validation.py` |
| `base_model.py` | `src/models/base.py` | `test_base_models.py` |
| `sensor_model.py` | `src/models/sensor.py` | `test_sensor_models.py` |

## Example Workflow

```bash
# 1. Copy stub to src
cp tdd/phase1_implementation_stubs/config_validation.py src/config/validation.py

# 2. Run tests
pytest tdd/phase1_foundation/config/test_config_validation.py -v

# 3. Fix any failing tests by adjusting the implementation

# 4. Move to next module
```

## Implementation Order

1. **Config Layer** (no dependencies)
   - `src/config/loader.py` - See PHASE1_QUICKSTART.md
   - `src/config/environment.py` - See PHASE1_QUICKSTART.md
   - `src/config/validation.py` - Use stub

2. **Utils Layer** (no dependencies)
   - `src/utils/logging_setup.py`
   - `src/utils/path_utils.py`
   - `src/utils/time_utils.py`

3. **Models Layer** (depends on utils for timestamps)
   - `src/models/base.py` - Use stub
   - `src/models/sensor.py` - Use stub
   - `src/models/video.py`
   - `src/models/chicken.py`

## Notes

- Stubs may need minor adjustments to pass all tests
- Read the test file to understand expected behavior
- Focus on making tests pass, not perfect code (refactor later)
