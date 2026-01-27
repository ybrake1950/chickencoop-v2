"""
Phase 8: Systemd Service Tests
==============================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates systemd service configuration:
- Service file structure and syntax
- Service dependencies (After, Wants)
- Restart behavior and recovery
- Environment variable configuration
- Working directory and user settings
- Log output configuration

WHY THIS MATTERS:
-----------------
Systemd services ensure the monitoring daemon runs continuously on each Pi.
Proper configuration ensures the service starts on boot, restarts after
failures, and logs appropriately. Misconfigured services can cause monitoring
outages.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase8_devops/services/test_systemd_services.py -v

Tests parse systemd service files and validate configuration.
"""
import pytest
import configparser
from pathlib import Path


@pytest.fixture
def service_file_path():
    """Get path to main service file."""
    return Path(__file__).parents[3] / 'config' / 'systemd' / 'chickencoop-monitor.service'


@pytest.fixture
def service_content(service_file_path):
    """Load service file content."""
    if service_file_path.exists():
        return service_file_path.read_text()
    return None


@pytest.fixture
def service_config(service_file_path):
    """Parse service file as INI config."""
    if not service_file_path.exists():
        return None

    config = configparser.ConfigParser()
    config.read(service_file_path)
    return config


class TestServiceFileExists:
    """Test service files exist."""

    def test_main_service_file_exists(self, service_file_path):
        """Main service file exists."""
        assert service_file_path.exists(), "chickencoop-monitor.service not found"

    def test_coop1_service_exists(self):
        """Coop1-specific service file exists."""
        path = Path(__file__).parents[3] / 'hardware' / 'deployment' / 'chickencoop-monitor-coop1.service'
        # May or may not exist
        if not path.exists():
            pytest.skip("Coop1-specific service not found")
        assert path.exists()

    def test_coop2_service_exists(self):
        """Coop2-specific service file exists."""
        path = Path(__file__).parents[3] / 'hardware' / 'deployment' / 'chickencoop-monitor-coop2.service'
        if not path.exists():
            pytest.skip("Coop2-specific service not found")
        assert path.exists()


class TestUnitSection:
    """Test [Unit] section configuration."""

    def test_has_description(self, service_config):
        """Service has description."""
        if service_config is None:
            pytest.skip("Service file not found")

        assert service_config.has_option('Unit', 'Description')
        desc = service_config.get('Unit', 'Description')
        assert len(desc) > 0

    def test_starts_after_network(self, service_config):
        """Service starts after network is online."""
        if service_config is None:
            pytest.skip("Service file not found")

        after = service_config.get('Unit', 'After', fallback='')
        assert 'network' in after.lower()

    def test_wants_network_online(self, service_config):
        """Service wants network-online.target."""
        if service_config is None:
            pytest.skip("Service file not found")

        wants = service_config.get('Unit', 'Wants', fallback='')
        assert 'network-online' in wants


class TestServiceSection:
    """Test [Service] section configuration."""

    def test_service_type(self, service_config):
        """Service type is configured."""
        if service_config is None:
            pytest.skip("Service file not found")

        service_type = service_config.get('Service', 'Type', fallback='')
        assert service_type in ['simple', 'forking', 'oneshot', 'notify']

    def test_runs_as_pi_user(self, service_config):
        """Service runs as pi user."""
        if service_config is None:
            pytest.skip("Service file not found")

        user = service_config.get('Service', 'User', fallback='')
        assert user == 'pi'

    def test_has_working_directory(self, service_config):
        """Service has working directory set."""
        if service_config is None:
            pytest.skip("Service file not found")

        workdir = service_config.get('Service', 'WorkingDirectory', fallback='')
        assert len(workdir) > 0
        assert 'coop' in workdir.lower()

    def test_has_exec_start(self, service_config):
        """Service has ExecStart command."""
        if service_config is None:
            pytest.skip("Service file not found")

        exec_start = service_config.get('Service', 'ExecStart', fallback='')
        assert len(exec_start) > 0

    def test_exec_start_uses_venv(self, service_config):
        """ExecStart uses virtual environment."""
        if service_config is None:
            pytest.skip("Service file not found")

        exec_start = service_config.get('Service', 'ExecStart', fallback='')
        assert 'venv' in exec_start

    def test_exec_start_runs_main(self, service_config):
        """ExecStart runs the main module."""
        if service_config is None:
            pytest.skip("Service file not found")

        exec_start = service_config.get('Service', 'ExecStart', fallback='')
        assert 'main' in exec_start or 'hardware' in exec_start


class TestRestartBehavior:
    """Test restart configuration."""

    def test_restart_always(self, service_config):
        """Service restarts on failure."""
        if service_config is None:
            pytest.skip("Service file not found")

        restart = service_config.get('Service', 'Restart', fallback='')
        assert restart in ['always', 'on-failure']

    def test_restart_delay(self, service_config):
        """Service has restart delay."""
        if service_config is None:
            pytest.skip("Service file not found")

        restart_sec = service_config.get('Service', 'RestartSec', fallback='')
        if restart_sec:
            assert int(restart_sec) >= 5, "Restart delay should be at least 5 seconds"


class TestEnvironmentConfiguration:
    """Test environment variable configuration."""

    def test_sets_coop_id(self, service_content):
        """Service sets COOP_ID environment variable."""
        if service_content is None:
            pytest.skip("Service file not found")

        assert 'COOP_ID' in service_content

    def test_environment_format(self, service_config):
        """Environment is properly formatted."""
        if service_config is None:
            pytest.skip("Service file not found")

        env = service_config.get('Service', 'Environment', fallback='')
        if env:
            # Should be quoted key=value format
            assert '=' in env


class TestLogging:
    """Test logging configuration."""

    def test_stdout_to_log_file(self, service_config):
        """Standard output goes to log file."""
        if service_config is None:
            pytest.skip("Service file not found")

        stdout = service_config.get('Service', 'StandardOutput', fallback='')
        assert 'append' in stdout or 'file' in stdout or 'journal' in stdout

    def test_stderr_to_log_file(self, service_config):
        """Standard error goes to log file."""
        if service_config is None:
            pytest.skip("Service file not found")

        stderr = service_config.get('Service', 'StandardError', fallback='')
        assert 'append' in stderr or 'file' in stderr or 'journal' in stderr

    def test_log_path_in_coop_directory(self, service_config):
        """Log files are in coop directory."""
        if service_config is None:
            pytest.skip("Service file not found")

        stdout = service_config.get('Service', 'StandardOutput', fallback='')
        if 'append:' in stdout or 'file:' in stdout:
            assert 'coop' in stdout.lower() or 'log' in stdout.lower()


class TestInstallSection:
    """Test [Install] section configuration."""

    def test_wanted_by_multiuser(self, service_config):
        """Service wanted by multi-user.target."""
        if service_config is None:
            pytest.skip("Service file not found")

        wanted_by = service_config.get('Install', 'WantedBy', fallback='')
        assert 'multi-user.target' in wanted_by


class TestExecStartPre:
    """Test pre-start commands."""

    def test_cleans_video_directory(self, service_content):
        """Service cleans video directory before start."""
        if service_content is None:
            pytest.skip("Service file not found")

        # May have ExecStartPre to clean temp files
        if 'ExecStartPre' in service_content:
            has_cleanup = 'video' in service_content.lower() or \
                         'find' in service_content or \
                         'rm' in service_content
            assert has_cleanup


class TestServiceManagementScript:
    """Test manage-services.sh script."""

    @pytest.fixture
    def manage_script_path(self):
        """Get path to manage-services.sh."""
        return Path(__file__).parents[3] / 'scripts' / 'manage-services.sh'

    @pytest.fixture
    def manage_script_content(self, manage_script_path):
        """Load manage-services.sh content."""
        if manage_script_path.exists():
            return manage_script_path.read_text()
        return None

    def test_manage_script_exists(self, manage_script_path):
        """manage-services.sh exists."""
        assert manage_script_path.exists(), "manage-services.sh not found"

    def test_supports_start_command(self, manage_script_content):
        """Script supports start command."""
        if manage_script_content is None:
            pytest.skip("manage-services.sh not found")

        assert 'start' in manage_script_content

    def test_supports_stop_command(self, manage_script_content):
        """Script supports stop command."""
        if manage_script_content is None:
            pytest.skip("manage-services.sh not found")

        assert 'stop' in manage_script_content

    def test_supports_restart_command(self, manage_script_content):
        """Script supports restart command."""
        if manage_script_content is None:
            pytest.skip("manage-services.sh not found")

        assert 'restart' in manage_script_content

    def test_supports_status_command(self, manage_script_content):
        """Script supports status command."""
        if manage_script_content is None:
            pytest.skip("manage-services.sh not found")

        assert 'status' in manage_script_content

    def test_supports_logs_command(self, manage_script_content):
        """Script supports logs command."""
        if manage_script_content is None:
            pytest.skip("manage-services.sh not found")

        assert 'log' in manage_script_content.lower()


class TestInstallServicesScript:
    """Test install-services.sh script."""

    @pytest.fixture
    def install_script_path(self):
        """Get path to install-services.sh."""
        return Path(__file__).parents[3] / 'scripts' / 'install-services.sh'

    @pytest.fixture
    def install_script_content(self, install_script_path):
        """Load install-services.sh content."""
        if install_script_path.exists():
            return install_script_path.read_text()
        return None

    def test_install_script_exists(self, install_script_path):
        """install-services.sh exists."""
        assert install_script_path.exists(), "install-services.sh not found"

    def test_detects_coop_by_hostname(self, install_script_content):
        """Detects coop by hostname."""
        if install_script_content is None:
            pytest.skip("install-services.sh not found")

        assert 'hostname' in install_script_content.lower()

    def test_copies_service_files(self, install_script_content):
        """Copies service files to systemd."""
        if install_script_content is None:
            pytest.skip("install-services.sh not found")

        assert '/etc/systemd/system' in install_script_content

    def test_reloads_systemd_daemon(self, install_script_content):
        """Reloads systemd daemon after install."""
        if install_script_content is None:
            pytest.skip("install-services.sh not found")

        assert 'daemon-reload' in install_script_content

    def test_enables_service(self, install_script_content):
        """Enables service for auto-start."""
        if install_script_content is None:
            pytest.skip("install-services.sh not found")

        assert 'systemctl enable' in install_script_content

    def test_secures_iot_certificates(self, install_script_content):
        """Secures IoT certificates with chmod."""
        if install_script_content is None:
            pytest.skip("install-services.sh not found")

        # Should chmod 600 on private keys
        has_security = '600' in install_script_content or \
                      'chmod' in install_script_content
        assert has_security, "Should secure certificate files"
