# Phase 1 Quick Start Guide - Starting From Nothing

This guide provides step-by-step instructions to initiate Phase 1 (Foundation) of the chicken coop monitoring system using Test-Driven Development.

## Prerequisites

- Python 3.11+ installed
- Git installed
- Terminal/command line access
- Text editor or IDE (VS Code recommended)

---

## Step 1: Create Project Structure

```bash
# Create a new project directory (or use existing)
mkdir -p chickencoop-v2
cd chickencoop-v2

# Initialize git repository
git init

# Create the source code directory structure
mkdir -p src/config
mkdir -p src/utils
mkdir -p src/models

# Create __init__.py files to make packages
touch src/__init__.py
touch src/config/__init__.py
touch src/utils/__init__.py
touch src/models/__init__.py

# Create data and logs directories (gitignored)
mkdir -p data logs

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
.venv/

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Project specific
data/
logs/
*.db
.env
config/certs/

# OS
.DS_Store
Thumbs.db
EOF
```

---

## Step 2: Set Up Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On Linux/macOS:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate

# Verify Python version
python --version  # Should be 3.11+
```

---

## Step 3: Install Testing Dependencies

```bash
# Create requirements-dev.txt for testing
cat > requirements-dev.txt << 'EOF'
# Testing
pytest==8.0.0
pytest-cov==4.1.0
pytest-mock==3.12.0

# Mocking AWS
moto==5.0.0

# Time mocking
freezegun==1.4.0

# Type checking (optional but recommended)
mypy==1.8.0

# Linting
pylint==3.0.0
black==24.1.0
EOF

# Install dependencies
pip install -r requirements-dev.txt
```

---

## Step 4: Copy TDD Test Files

Copy the `tdd/` directory from this repository to your new project, or create the structure manually.

```bash
# If copying from existing repo:
cp -r /path/to/chickencoop-monitoring/tdd ./

# Verify structure
ls -la tdd/phase1_foundation/
```

You should see:
```
tdd/phase1_foundation/
├── config/
│   ├── test_config_loader.py
│   ├── test_config_validation.py
│   └── test_environment.py
├── utils/
│   ├── test_logging_setup.py
│   ├── test_path_utils.py
│   └── test_time_utils.py
└── models/
    ├── test_base_models.py
    ├── test_sensor_models.py
    ├── test_video_models.py
    └── test_chicken_models.py
```

---

## Step 5: Run Tests (Expect Failures)

```bash
# Run all Phase 1 tests - they WILL fail (this is expected!)
pytest tdd/phase1_foundation/ -v

# You'll see errors like:
# ModuleNotFoundError: No module named 'src.config.loader'
```

This is the **RED** phase of TDD - tests fail because no implementation exists yet.

---

## Step 6: Implementation Order

Work through these files in order. Each builds on the previous.

### 6.1 Configuration Loader (Start Here)

**Test file:** `tdd/phase1_foundation/config/test_config_loader.py`

**Run the tests:**
```bash
pytest tdd/phase1_foundation/config/test_config_loader.py -v
```

**Create implementation file:**
```bash
touch src/config/loader.py
```

**Implement `src/config/loader.py`:**
```python
"""
Configuration file loading utilities.

This module handles loading JSON configuration files with support for
merging base and device-specific configurations.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


def load_config(path: Path) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.

    Args:
        path: Path to the configuration file

    Returns:
        Dictionary containing configuration data

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    content = path.read_text()
    if not content.strip():
        raise json.JSONDecodeError("Empty file", content, 0)

    return json.loads(content)


def load_aws_config(path: Path) -> Dict[str, Any]:
    """Load AWS configuration from a JSON file."""
    return load_config(path)


def load_device_config(path: Path) -> Dict[str, Any]:
    """Load device-specific configuration from a JSON file."""
    return load_config(path)


def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two configuration dictionaries.

    Override values take precedence. Nested dictionaries are merged recursively.

    Args:
        base: Base configuration dictionary
        override: Override configuration dictionary

    Returns:
        Merged configuration dictionary
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value

    return result


def get_config_path(filename: str) -> Path:
    """
    Get the path to a configuration file.

    Uses CONFIG_DIR environment variable if set, otherwise defaults
    to 'config' directory relative to project root.

    Args:
        filename: Name of the configuration file

    Returns:
        Path to the configuration file
    """
    config_dir = os.environ.get("CONFIG_DIR")
    if config_dir:
        return Path(config_dir) / filename

    # Default to config directory relative to project root
    return Path(__file__).parent.parent.parent / "config" / filename


def get_device_config_path() -> Path:
    """
    Get the path to the device-specific configuration file.

    Uses COOP_ID environment variable to determine which device config to load.

    Returns:
        Path to the device configuration file
    """
    coop_id = os.environ.get("COOP_ID", "default")
    return get_config_path(f"devices/{coop_id}.json")
```

**Run tests again:**
```bash
pytest tdd/phase1_foundation/config/test_config_loader.py -v
```

Tests should now pass (GREEN phase).

---

### 6.2 Environment Variables

**Test file:** `tdd/phase1_foundation/config/test_environment.py`

**Create implementation:**
```bash
touch src/config/environment.py
```

**Implement `src/config/environment.py`:**
```python
"""
Environment variable handling utilities.

Provides typed access to environment variables with defaults,
validation, and special handling for common configuration values.
"""

import os
from typing import Optional


class MissingEnvironmentVariable(Exception):
    """Raised when a required environment variable is not set."""
    pass


def get_env(name: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Get an environment variable value.

    Args:
        name: Name of the environment variable
        default: Default value if not set
        required: If True, raise exception when not set

    Returns:
        The environment variable value or default

    Raises:
        MissingEnvironmentVariable: If required and not set
    """
    value = os.environ.get(name)

    if value is None:
        if required:
            raise MissingEnvironmentVariable(f"Required environment variable not set: {name}")
        return default

    return value


def get_env_int(name: str, default: Optional[int] = None) -> Optional[int]:
    """Get an environment variable as an integer."""
    value = os.environ.get(name)

    if value is None:
        return default

    return int(value)


def get_env_float(name: str, default: Optional[float] = None) -> Optional[float]:
    """Get an environment variable as a float."""
    value = os.environ.get(name)

    if value is None:
        return default

    return float(value)


def get_env_bool(name: str, default: bool = False) -> bool:
    """
    Get an environment variable as a boolean.

    Truthy values: 'true', 'True', 'TRUE', '1', 'yes', 'Yes'
    Falsy values: 'false', 'False', 'FALSE', '0', 'no', 'No'
    """
    value = os.environ.get(name)

    if value is None:
        return default

    return value.lower() in ('true', '1', 'yes')


def get_coop_id() -> str:
    """
    Get the COOP_ID environment variable.

    Returns normalized (lowercase) coop ID, defaults to 'default'.
    """
    coop_id = os.environ.get("COOP_ID", "default")
    return coop_id.lower()


def is_testing() -> bool:
    """Check if running in test mode."""
    return get_env_bool("TESTING", default=False)


def is_production() -> bool:
    """Check if running in production mode."""
    return not is_testing()


def get_secret_key() -> str:
    """
    Get the SECRET_KEY for Flask sessions.

    In testing mode, returns a default test key.
    In production, requires the environment variable to be set.

    Raises:
        MissingEnvironmentVariable: If not set in production
    """
    if is_testing():
        return os.environ.get("SECRET_KEY", "test-secret-key-not-for-production")

    value = os.environ.get("SECRET_KEY")
    if value is None:
        raise MissingEnvironmentVariable("SECRET_KEY must be set in production")

    return value


def get_aws_region() -> str:
    """
    Get the AWS region.

    Checks AWS_REGION first, then AWS_DEFAULT_REGION, defaults to 'us-east-1'.
    """
    return os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
```

**Run tests:**
```bash
pytest tdd/phase1_foundation/config/test_environment.py -v
```

---

### 6.3 Continue With Remaining Files

Follow the same pattern for each file:

1. **Run the test** → See failures
2. **Create the implementation file** → Write minimal code
3. **Run tests again** → See them pass
4. **Refactor if needed** → Keep tests green

**Implementation order:**
```
1. src/config/loader.py          ← Done
2. src/config/environment.py     ← Done
3. src/config/validation.py      ← Next
4. src/utils/logging_setup.py
5. src/utils/path_utils.py
6. src/utils/time_utils.py
7. src/models/base.py
8. src/models/sensor.py
9. src/models/video.py
10. src/models/chicken.py
```

---

## Step 7: Create Sample Configuration Files

For tests to pass, you'll need sample config files:

```bash
mkdir -p config/devices

# Create main config.json
cat > config/config.json << 'EOF'
{
  "sensors": {
    "read_interval": 300,
    "temperature": {
      "min_threshold": 32,
      "max_threshold": 95,
      "unit": "fahrenheit"
    },
    "humidity": {
      "min_threshold": 30,
      "max_threshold": 80
    }
  },
  "camera": {
    "resolution": [1280, 720],
    "framerate": 24,
    "rotation": 0
  },
  "motion": {
    "enabled": true,
    "sensitivity": 50,
    "min_area": 500,
    "recording_duration": 30
  },
  "headcount": {
    "enabled": true,
    "schedule_time": "19:00",
    "expected_count": 6
  }
}
EOF

# Create AWS config
cat > config/aws_config.json << 'EOF'
{
  "region": "us-east-1",
  "s3": {
    "bucket": "chickencoop-bucket",
    "video_prefix": "videos/",
    "csv_prefix": "csv/"
  },
  "iot": {
    "endpoint": "your-iot-endpoint.iot.us-east-1.amazonaws.com",
    "thing_name": "chickencoop",
    "topic_prefix": "chickencoop"
  },
  "sns": {
    "topic_arn": "arn:aws:sns:us-east-1:123456789:alerts"
  }
}
EOF

# Create device config
cat > config/devices/coop1.json << 'EOF'
{
  "device_id": "coop1",
  "device_type": "raspberry_pi_3b",
  "camera": {
    "resolution": [1280, 720],
    "framerate": 24
  }
}
EOF
```

---

## Step 8: Verify Phase 1 Complete

When all implementations are done:

```bash
# Run all Phase 1 tests
pytest tdd/phase1_foundation/ -v

# Run with coverage report
pytest tdd/phase1_foundation/ -v --cov=src --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
# or: xdg-open htmlcov/index.html  # Linux
```

**Success criteria:**
- All tests pass (green)
- Coverage > 80%
- No linting errors: `pylint src/`

---

## Step 9: Commit Your Work

```bash
git add .
git commit -m "Complete Phase 1: Foundation layer

Implemented:
- Configuration loading and validation
- Environment variable handling
- Logging setup utilities
- Path manipulation utilities
- Timestamp handling utilities
- Base model classes
- Sensor, Video, Chicken data models

All Phase 1 tests passing with >80% coverage."
```

---

## Quick Reference: TDD Cycle

```
┌─────────────────────────────────────────────────┐
│                  TDD CYCLE                       │
├─────────────────────────────────────────────────┤
│                                                  │
│   1. RED    → Run test, watch it fail           │
│                                                  │
│   2. GREEN  → Write minimal code to pass        │
│                                                  │
│   3. REFACTOR → Improve code, keep tests green  │
│                                                  │
│   4. REPEAT → Move to next test                 │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## Common Issues

### Import Errors
```bash
# Ensure src is in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or add to pytest.ini:
# [pytest]
# pythonpath = .
```

### Test Discovery
```bash
# If tests aren't found, check naming:
# - Test files must start with test_
# - Test functions must start with test_
# - Test classes must start with Test
```

### Fixture Not Found
```bash
# Ensure conftest.py is in the tdd/ directory
# Fixtures defined there are available to all tests
```

---

## Next Steps

After Phase 1 is complete:
1. Review code for quality improvements
2. Add docstrings to all public functions
3. Run linting: `pylint src/ --errors-only`
4. Move to Phase 2: Hardware Abstraction

```bash
pytest tdd/phase2_hardware/ -v
```
