"""Path utilities for the chickencoop project."""

import os
import re
from pathlib import Path
from datetime import datetime, date
from typing import Optional


def get_project_root() -> Path:
    """
    Get the project root directory.

    Searches upward from the current file location for common project markers
    (pyproject.toml, setup.py, requirements.txt, .git).

    Returns:
        Path to the project root directory
    """
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        markers = ["pyproject.toml", "setup.py", "requirements.txt", ".git"]
        if any((parent / marker).exists() for marker in markers):
            return parent
    return current.parent.parent.parent


def get_config_dir() -> Path:
    """
    Get the config directory.

    Returns:
        Path to the config directory within project root
    """
    return get_project_root() / "config"


def get_data_dir() -> Path:
    """
    Get the data directory.

    Returns:
        Path to the data directory within project root
    """
    return get_project_root() / "data"


def get_logs_dir() -> Path:
    """
    Get the logs directory.

    Returns:
        Path to the logs directory within project root
    """
    return get_project_root() / "logs"


def get_certs_dir() -> Path:
    """
    Get the certs directory.

    Returns:
        Path to the certs directory within project root
    """
    return get_project_root() / "certs"


def ensure_dir(path: Path) -> Path:
    """
    Ensure directory exists, creating it if necessary.

    Args:
        path: Path to the directory

    Returns:
        The path to the directory

    Raises:
        FileExistsError: If path exists but is not a directory
    """
    path = Path(path)
    if path.exists() and not path.is_dir():
        raise FileExistsError(f"Path exists but is not a directory: {path}")
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_video_path(
    camera: str, timestamp: datetime, trigger: Optional[str] = None
) -> Path:
    """
    Generate video file path.

    Args:
        camera: Camera identifier (e.g., 'indoor', 'outdoor')
        timestamp: Timestamp for the video
        trigger: Optional trigger type (e.g., 'motion')

    Returns:
        Path to the video file within the data/videos directory
    """
    date_str = timestamp.strftime("%Y%m%d_%H%M%S")
    prefix = "motion_" if trigger == "motion" else ""
    filename = f"{prefix}{camera}_{date_str}.mp4"
    return get_data_dir() / "videos" / filename


def get_csv_path(date: date) -> Path:  # pylint: disable=redefined-outer-name
    """
    Generate CSV file path for sensor data.

    Args:
        date: Date for the CSV file

    Returns:
        Path to the CSV file within the data/csv directory
    """
    date_str = date.strftime("%Y-%m-%d")
    filename = f"sensor_data_{date_str}.csv"
    return get_data_dir() / "csv" / filename


def get_s3_video_key(filename: str) -> str:
    """
    Generate S3 key for video.

    Args:
        filename: Video filename

    Returns:
        S3 key in format {coop_id}/videos/{filename}
    """
    coop_id = os.environ.get("COOP_ID", "default")
    return f"{coop_id}/videos/{filename}"


def get_s3_csv_key(filename: str) -> str:
    """
    Generate S3 key for CSV.

    Args:
        filename: CSV filename

    Returns:
        S3 key in format {coop_id}/csv/{filename}
    """
    coop_id = os.environ.get("COOP_ID", "default")
    return f"{coop_id}/csv/{filename}"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing special characters.

    Replaces spaces with underscores and removes characters that are
    invalid in filenames on common operating systems.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for filesystem use
    """
    if not filename:
        return filename
    filename = filename.replace(" ", "_")
    filename = re.sub(r'[<>:"|?*]', "", filename)
    return filename
