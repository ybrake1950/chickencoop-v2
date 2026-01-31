"""
Phase 17: Data Backup Tests
===========================

FUNCTIONALITY BEING TESTED:
---------------------------
- Scheduled video backup to external storage
- Configuration backup and versioning
- Backup verification and integrity
- Backup encryption

WHY THIS MATTERS:
-----------------
Data backup protects against hardware failure, accidental deletion,
and corruption. Regular backups with verification ensure data can
be recovered when needed.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase17_backup_dr/backup/test_data_backup.py -v
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from src.backup.data_backup import (
    BackupManager,
    BackupConfig,
    BackupTarget,
    BackupVerifier,
    BackupEncryption,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def backup_manager():
    """Provide a backup manager."""
    config = BackupConfig(
        targets=[
            BackupTarget(type="usb", path="/mnt/usb/backup"),
            BackupTarget(type="nas", path="//nas/backup"),
        ],
        retention_days=30,
    )
    return BackupManager(config=config)


@pytest.fixture
def verifier():
    """Provide a backup verifier."""
    return BackupVerifier()


@pytest.fixture
def encryption():
    """Provide backup encryption."""
    return BackupEncryption(key_id="backup-key-001")


# =============================================================================
# TestVideoBackup
# =============================================================================

class TestVideoBackup:
    """Test video backup functionality."""

    @patch("src.backup.data_backup.shutil.copy2")
    def test_backup_to_usb(self, mock_copy, backup_manager):
        """Videos backed up to USB drive."""
        result = backup_manager.backup_videos(target_type="usb")
        assert result.success is True
        assert result.target_type == "usb"
        assert result.files_copied >= 0

    @patch("src.backup.data_backup.shutil.copy2")
    def test_backup_to_nas(self, mock_copy, backup_manager):
        """Videos backed up to NAS."""
        result = backup_manager.backup_videos(target_type="nas")
        assert result.success is True
        assert result.target_type == "nas"

    @patch("src.backup.data_backup.shutil.copy2")
    def test_incremental_backup(self, mock_copy, backup_manager):
        """Incremental backup only copies new files."""
        backup_manager.set_mode("incremental")
        result = backup_manager.backup_videos(target_type="usb")
        assert result.success is True
        assert result.mode == "incremental"
        assert result.skipped_unchanged >= 0

    def test_backup_schedule(self, backup_manager):
        """Backup runs on schedule."""
        backup_manager.set_schedule(hour=2, minute=0)
        assert backup_manager.schedule_hour == 2
        assert backup_manager.schedule_minute == 0

    def test_backup_retention(self, backup_manager):
        """Old backups cleaned per retention policy."""
        assert backup_manager.config.retention_days == 30
        now = datetime.now(timezone.utc)
        old_backup = MagicMock(
            created_at=now - timedelta(days=45),
            path="/mnt/usb/backup/old.tar"
        )
        should_delete = backup_manager.should_purge(old_backup)
        assert should_delete is True

        recent_backup = MagicMock(
            created_at=now - timedelta(days=5),
            path="/mnt/usb/backup/recent.tar"
        )
        should_delete = backup_manager.should_purge(recent_backup)
        assert should_delete is False


# =============================================================================
# TestConfigBackup
# =============================================================================

class TestConfigBackup:
    """Test configuration backup."""

    def test_config_exported(self, backup_manager):
        """Configuration exported to file."""
        result = backup_manager.export_config()
        assert result is not None
        assert result.format in ("json", "yaml")
        assert len(result.content) > 0

    def test_config_versioned(self, backup_manager):
        """Configuration versions maintained."""
        backup_manager.export_config()
        backup_manager.export_config()
        versions = backup_manager.get_config_versions()
        assert len(versions) >= 2
        assert versions[0].version != versions[1].version

    def test_config_diff_available(self, backup_manager):
        """Diff between versions available."""
        backup_manager.export_config()
        backup_manager.update_config({"temperature_threshold": 105})
        backup_manager.export_config()
        versions = backup_manager.get_config_versions()
        diff = backup_manager.config_diff(versions[0].version, versions[1].version)
        assert diff is not None
        assert len(diff.changes) > 0

    def test_config_backup_on_change(self, backup_manager):
        """Config backed up on every change."""
        backup_manager.enable_auto_backup()
        assert backup_manager.auto_backup_enabled is True
        backup_manager.update_config({"humidity_threshold": 80})
        versions = backup_manager.get_config_versions()
        assert len(versions) >= 1


# =============================================================================
# TestBackupVerification
# =============================================================================

class TestBackupVerification:
    """Test backup verification."""

    def test_checksum_verification(self, verifier):
        """Backup files verified with checksums."""
        backup = MagicMock(
            path="/mnt/usb/backup/2024-01-01.tar",
            checksum="sha256:abc123"
        )
        result = verifier.verify_checksum(backup)
        assert result.verified is True
        assert result.algorithm == "sha256"

    def test_restore_test(self, verifier):
        """Backup can be restored successfully."""
        backup = MagicMock(path="/mnt/usb/backup/2024-01-01.tar")
        result = verifier.test_restore(backup, target_dir="/tmp/restore_test")
        assert result.success is True
        assert result.files_restored > 0

    def test_verification_logged(self, verifier, caplog):
        """Verification results logged."""
        import logging
        caplog.set_level(logging.INFO)
        backup = MagicMock(
            path="/mnt/usb/backup/2024-01-01.tar",
            checksum="sha256:abc123"
        )
        verifier.verify_checksum(backup)
        assert len(caplog.records) > 0

    def test_verification_alerts(self, verifier):
        """Failed verification triggers alert."""
        backup = MagicMock(
            path="/mnt/usb/backup/corrupted.tar",
            checksum="sha256:wrong"
        )
        verifier.set_computed_checksum("sha256:different")
        result = verifier.verify_checksum(backup)
        assert result.verified is False
        assert result.alert_sent is True


# =============================================================================
# TestBackupEncryption
# =============================================================================

class TestBackupEncryption:
    """Test backup encryption."""

    def test_backup_encrypted(self, encryption):
        """Backups are encrypted."""
        data = b"sensitive coop configuration data"
        encrypted = encryption.encrypt(data)
        assert encrypted != data
        assert len(encrypted) > 0

    def test_encryption_key_management(self, encryption):
        """Encryption keys properly managed."""
        assert encryption.key_id is not None
        assert encryption.key_id == "backup-key-001"
        keys = encryption.list_keys()
        assert len(keys) >= 1
        assert any(k.key_id == "backup-key-001" for k in keys)

    def test_encrypted_backup_restorable(self, encryption):
        """Encrypted backups can be restored."""
        original = b"important backup data for chickens"
        encrypted = encryption.encrypt(original)
        decrypted = encryption.decrypt(encrypted)
        assert decrypted == original


# =============================================================================
# TestEdgeCases
# =============================================================================

class TestEdgeCases:
    """Test edge cases for full coverage."""

    def test_backup_unknown_target(self, backup_manager):
        """Backup with unknown target type returns failure."""
        result = backup_manager.backup_videos(target_type="cloud")
        assert result.success is False
        assert result.target_type == "cloud"

    def test_config_diff_invalid_version(self, backup_manager):
        """Config diff with nonexistent version returns None."""
        backup_manager.export_config()
        result = backup_manager.config_diff("v1", "v999")
        assert result is None
