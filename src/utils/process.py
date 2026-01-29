"""
Safe subprocess execution utilities.
"""

import subprocess
from typing import List, Optional


def run_command(args: List[str], shell: bool = False, timeout: Optional[int] = 30) -> subprocess.CompletedProcess:
    """Run a command safely using list arguments.

    Args:
        args: Command and arguments as a list.
        shell: Whether to use shell execution (default False).
        timeout: Command timeout in seconds.

    Returns:
        CompletedProcess instance with returncode, stdout, stderr.
    """
    return subprocess.run(
        args,
        shell=shell,
        timeout=timeout,
        capture_output=True,
        text=True,
    )
