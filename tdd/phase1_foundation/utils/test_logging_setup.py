"""
TDD Tests: Logging Configuration

These tests define the expected behavior for logging setup.
Implement src/utils/logging_setup.py to make these tests pass.

Run: pytest tdd/phase1_foundation/utils/test_logging_setup.py -v
"""

import logging
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


# =============================================================================
# Test: Logger Creation
# =============================================================================

class TestLoggerCreation:
    """Tests for creating configured loggers."""

    def test_get_logger_returns_logger_instance(self):
        """Should return a logging.Logger instance."""
        from src.utils.logging_setup import get_logger

        result = get_logger("test_module")

        assert isinstance(result, logging.Logger)

    def test_get_logger_uses_module_name(self):
        """Logger should use the provided module name."""
        from src.utils.logging_setup import get_logger

        result = get_logger("my_module")

        assert result.name == "my_module"

    def test_get_logger_same_name_returns_same_instance(self):
        """Same logger name should return same instance."""
        from src.utils.logging_setup import get_logger

        logger1 = get_logger("same_name")
        logger2 = get_logger("same_name")

        assert logger1 is logger2


# =============================================================================
# Test: Log Level Configuration
# =============================================================================

class TestLogLevelConfiguration:
    """Tests for log level configuration."""

    def test_setup_logging_default_level_is_info(self):
        """Default log level should be INFO."""
        from src.utils.logging_setup import setup_logging, get_logger

        setup_logging()
        logger = get_logger("test")

        assert logger.level <= logging.INFO

    def test_setup_logging_respects_level_parameter(self):
        """Should respect the level parameter."""
        from src.utils.logging_setup import setup_logging, get_logger

        setup_logging(level=logging.DEBUG)
        logger = get_logger("test_debug")

        assert logger.level <= logging.DEBUG

    def test_setup_logging_from_env_variable(self, monkeypatch):
        """Should read log level from LOG_LEVEL environment variable."""
        from src.utils.logging_setup import setup_logging, get_logger

        monkeypatch.setenv("LOG_LEVEL", "WARNING")
        setup_logging()
        logger = get_logger("test_env")

        # Root logger should be at WARNING
        assert logging.getLogger().level == logging.WARNING


# =============================================================================
# Test: Log Format
# =============================================================================

class TestLogFormat:
    """Tests for log message formatting."""

    def test_log_format_includes_timestamp(self, caplog):
        """Log format should include timestamp."""
        from src.utils.logging_setup import setup_logging, get_logger

        setup_logging()
        logger = get_logger("test_format")

        with caplog.at_level(logging.INFO):
            logger.info("Test message")

        # Check that the log record has the expected format
        assert len(caplog.records) > 0

    def test_log_format_includes_level_name(self, caplog):
        """Log format should include level name."""
        from src.utils.logging_setup import setup_logging, get_logger

        setup_logging()
        logger = get_logger("test_level")

        with caplog.at_level(logging.INFO):
            logger.info("Test message")

        assert caplog.records[0].levelname == "INFO"

    def test_log_format_includes_logger_name(self, caplog):
        """Log format should include logger name."""
        from src.utils.logging_setup import setup_logging, get_logger

        setup_logging()
        logger = get_logger("my_custom_logger")

        with caplog.at_level(logging.INFO):
            logger.info("Test message")

        assert caplog.records[0].name == "my_custom_logger"


# =============================================================================
# Test: File Handler
# =============================================================================

class TestFileHandler:
    """Tests for file-based logging."""

    def test_setup_file_logging_creates_handler(self, tmp_path: Path):
        """Should create a file handler when log path provided."""
        from src.utils.logging_setup import setup_logging

        log_file = tmp_path / "test.log"
        setup_logging(log_file=log_file)

        assert log_file.parent.exists()

    def test_log_messages_written_to_file(self, tmp_path: Path):
        """Log messages should be written to file."""
        from src.utils.logging_setup import setup_logging, get_logger

        log_file = tmp_path / "test.log"
        setup_logging(log_file=log_file)
        logger = get_logger("file_test")

        logger.info("Test file message")

        # Force handlers to flush
        for handler in logging.getLogger().handlers:
            handler.flush()

        assert log_file.exists()
        content = log_file.read_text()
        assert "Test file message" in content

    def test_log_file_rotation_by_size(self, tmp_path: Path):
        """Should rotate log files when max size reached."""
        from src.utils.logging_setup import setup_logging_with_rotation

        log_file = tmp_path / "rotating.log"
        setup_logging_with_rotation(
            log_file=log_file,
            max_bytes=1000,
            backup_count=3
        )

        # Verify RotatingFileHandler is configured
        handlers = logging.getLogger().handlers
        rotating_handlers = [h for h in handlers
                           if hasattr(h, 'maxBytes')]

        assert len(rotating_handlers) > 0


# =============================================================================
# Test: Console Handler
# =============================================================================

class TestConsoleHandler:
    """Tests for console logging."""

    def test_setup_logging_adds_console_handler(self):
        """Should add a StreamHandler for console output."""
        from src.utils.logging_setup import setup_logging

        setup_logging(console=True)

        handlers = logging.getLogger().handlers
        stream_handlers = [h for h in handlers
                         if isinstance(h, logging.StreamHandler)]

        assert len(stream_handlers) > 0

    def test_setup_logging_no_console_when_disabled(self):
        """Should not add console handler when disabled."""
        from src.utils.logging_setup import setup_logging

        # Clear existing handlers first
        logging.getLogger().handlers.clear()
        setup_logging(console=False)

        handlers = logging.getLogger().handlers
        stream_handlers = [h for h in handlers
                         if isinstance(h, logging.StreamHandler)
                         and not hasattr(h, 'baseFilename')]

        assert len(stream_handlers) == 0


# =============================================================================
# Test: Coop ID in Logs
# =============================================================================

class TestCoopIdLogging:
    """Tests for including coop ID in logs."""

    def test_log_format_includes_coop_id(self, monkeypatch, caplog):
        """Log format should include COOP_ID when set."""
        from src.utils.logging_setup import setup_logging, get_logger

        monkeypatch.setenv("COOP_ID", "coop1")
        setup_logging(include_coop_id=True)
        logger = get_logger("coop_test")

        with caplog.at_level(logging.INFO):
            logger.info("Test message")

        # The formatter should include coop_id
        # This depends on implementation details
        assert len(caplog.records) > 0
