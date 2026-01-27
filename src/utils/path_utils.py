"""Path utilities for the chickencoop project."""

import os
import re
from pathlib import Path
from datetime import datetime, date


def get_project_root() -> Path:
    """Get the project root directory."""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        markers = ["pyproject.toml", "setup.py", "requirements.txt", ".git"]
        if any((parent / marker).exists() for marker in markers):
            return parent
    return current.parent.parent.parent


def get_config_dir() -> Path:
    """Get the config directory."""
    return get_project_root() / "config"


def get_data_dir() -> Path:
    """Get the data directory."""
    return get_project_root() / "data"


def get_logs_dir() -> Path:
    """Get the logs directory."""
    return get_project_root() / "logs"


def get_certs_dir() -> Path:
    """Get the certs directory."""
    return get_project_root() / "certs"


def ensure_dir(path: Path) -> Path:
    """Ensure directory exists, creating it if necessary."""
    path = Path(path)
    if path.exists() and not path.is_dir():
        raise FileExistsError(f"Path exists but is not a directory: {path}")
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_video_path(camera: str, timestamp: datetime, trigger: str = None) -> Path:
    """Generate video file path."""
    date_str = timestamp.strftime("%Y%m%d_%H%M%S")
    prefix = "motion_" if trigger == "motion" else ""
    filename = f"{prefix}{camera}_{date_str}.mp4"
    return get_data_dir() / "videos" / filename


def get_csv_path(date: date) -> Path:
    """Generate CSV file path."""
    date_str = date.strftime("%Y-%m-%d")
    filename = f"sensor_data_{date_str}.csv"
    return get_data_dir() / "csv" / filename


def get_s3_video_key(filename: str) -> str:
    """Generate S3 key for video."""
    coop_id = os.environ.get("COOP_ID", "default")
    return f"{coop_id}/videos/{filename}"


def get_s3_csv_key(filename: str) -> str:
    """Generate S3 key for CSV."""
    coop_id = os.environ.get("COOP_ID", "default")
    return f"{coop_id}/csv/{filename}"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing special characters."""
    if not filename:
        return filename
    filename = filename.replace(" ", "_")
    filename = re.sub(r'[<>:"|?*]', "", filename)
    return filename
