"""
Phase 28: Operations Documentation Tests
==========================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates that operational documentation exists:
- Deployment runbook (step-by-step production deployment)
- Troubleshooting guide (common issues and fixes)
- Monitoring guide (what to watch, how to respond)
- Backup and restore procedures

WHY THIS MATTERS:
-----------------
Without operations documentation, only the original developer can
deploy, troubleshoot, and maintain the system. Documentation enables
knowledge transfer, reduces mean time to recovery (MTTR), and ensures
the system can survive team changes.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase28_documentation/operations_docs/test_operations_docs.py -v
"""
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Get project root directory."""
    return Path(__file__).parents[3]


@pytest.fixture
def all_docs(project_root):
    """Find all markdown documentation files."""
    docs = []
    for md in project_root.rglob('*.md'):
        if '.git' not in str(md) and 'node_modules' not in str(md):
            docs.append(md)
    return docs


@pytest.fixture
def doc_content(all_docs):
    """Concatenate all documentation content."""
    content = ''
    for doc in all_docs:
        try:
            content += doc.read_text() + '\n'
        except (UnicodeDecodeError, PermissionError):
            continue
    return content.lower()


class TestDeploymentRunbook:
    """Verify deployment runbook exists."""

    def test_deployment_docs_exist(self, doc_content):
        """Deployment documentation must exist."""
        has_deploy = ('deploy' in doc_content and
                      ('step' in doc_content or
                       'guide' in doc_content or
                       'runbook' in doc_content or
                       'instructions' in doc_content))
        assert has_deploy, (
            "No deployment runbook found. Create a step-by-step guide "
            "for deploying to production Raspberry Pis."
        )

    def test_deployment_covers_prerequisites(self, doc_content):
        """Deployment docs must cover prerequisites."""
        has_prereqs = ('prerequisite' in doc_content or
                       'requirement' in doc_content or
                       'before you' in doc_content or
                       'python' in doc_content)
        assert has_prereqs, (
            "Deployment docs should cover prerequisites (Python, OS, etc.)"
        )


class TestTroubleshootingGuide:
    """Verify troubleshooting guide exists."""

    def test_troubleshooting_docs_exist(self, doc_content):
        """Troubleshooting documentation must exist."""
        has_troubleshoot = ('troubleshoot' in doc_content or
                            'common issue' in doc_content or
                            'debug' in doc_content or
                            'problem' in doc_content)
        assert has_troubleshoot, (
            "No troubleshooting guide found. Document common issues "
            "and their solutions."
        )


class TestMonitoringGuide:
    """Verify monitoring guide exists."""

    def test_monitoring_docs_exist(self, doc_content):
        """Monitoring documentation must exist."""
        has_monitor = ('monitor' in doc_content or
                       'observ' in doc_content or
                       'metric' in doc_content or
                       'alert' in doc_content or
                       'cloudwatch' in doc_content)
        assert has_monitor, (
            "No monitoring guide found. Document what to watch "
            "and how to respond to alerts."
        )


class TestBackupRestoreDocs:
    """Verify backup and restore documentation exists."""

    def test_backup_docs_exist(self, doc_content):
        """Backup and restore documentation must exist."""
        has_backup = ('backup' in doc_content or
                      'restore' in doc_content or
                      'recovery' in doc_content or
                      'disaster' in doc_content)
        assert has_backup, (
            "No backup/restore documentation found. Document how to "
            "back up and restore the system."
        )
