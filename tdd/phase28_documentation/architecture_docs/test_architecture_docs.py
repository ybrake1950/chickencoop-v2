"""
Phase 28: Architecture Documentation Tests
============================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates that architecture documentation exists:
- System architecture overview (Pi ↔ AWS ↔ Frontend)
- Data flow documentation (sensor reading lifecycle)
- Network topology documentation (Pi WiFi, AWS services, user access)
- Phase dependency hierarchy is documented

WHY THIS MATTERS:
-----------------
Architecture documentation enables new developers to understand the
system without reading every source file. It captures design decisions,
component interactions, and deployment topology that aren't obvious
from code alone.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase28_documentation/architecture_docs/test_architecture_docs.py -v
"""
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Get project root directory."""
    return Path(__file__).parents[3]


@pytest.fixture
def all_docs(project_root):
    """Find all documentation files."""
    docs = []
    for ext in ['*.md', '*.rst', '*.txt']:
        for f in project_root.rglob(ext):
            if '.git' not in str(f) and 'node_modules' not in str(f):
                docs.append(f)
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


class TestSystemArchitecture:
    """Verify system architecture is documented."""

    def test_architecture_overview_exists(self, doc_content):
        """System architecture overview must be documented."""
        has_arch = ('architecture' in doc_content or
                    'system overview' in doc_content or
                    'system design' in doc_content or
                    'component' in doc_content)
        assert has_arch, (
            "No system architecture documentation found. "
            "Document the Pi ↔ AWS ↔ Frontend topology."
        )

    def test_aws_services_documented(self, doc_content):
        """AWS services used must be documented."""
        aws_services = ['s3', 'iot', 'sns', 'dynamodb', 'lambda', 'cloudwatch']
        found = sum(1 for s in aws_services if s in doc_content)
        assert found >= 3, (
            f"Only {found}/6 AWS services documented. "
            "Document all AWS services: S3, IoT, SNS, DynamoDB, Lambda, CloudWatch."
        )


class TestDataFlowDocumentation:
    """Verify data flow is documented."""

    def test_sensor_data_flow_documented(self, doc_content):
        """Sensor data flow must be documented."""
        has_flow = ('sensor' in doc_content and
                    ('flow' in doc_content or
                     'pipeline' in doc_content or
                     'data' in doc_content))
        assert has_flow, (
            "Sensor data flow not documented. "
            "Document: sensor → CSV → S3 → dashboard"
        )

    def test_video_data_flow_documented(self, doc_content):
        """Video data flow must be documented."""
        has_video = ('video' in doc_content and
                     ('s3' in doc_content or
                      'storage' in doc_content or
                      'record' in doc_content))
        assert has_video, (
            "Video data flow not documented. "
            "Document: motion → recording → S3 → dashboard"
        )


class TestPhaseDocumentation:
    """Verify TDD phase documentation is complete."""

    def test_tdd_readme_exists(self, project_root):
        """tdd/README.md must exist."""
        readme = project_root / 'tdd' / 'README.md'
        assert readme.exists(), "tdd/README.md not found"

    def test_tdd_catalog_exists(self, project_root):
        """tdd/TDD_CATALOG.md must exist."""
        catalog = project_root / 'tdd' / 'TDD_CATALOG.md'
        assert catalog.exists(), "tdd/TDD_CATALOG.md not found"

    def test_tdd_catalog_covers_all_phases(self, project_root):
        """TDD_CATALOG.md must cover all phases including 19-28."""
        catalog = project_root / 'tdd' / 'TDD_CATALOG.md'
        if not catalog.exists():
            pytest.skip("TDD_CATALOG.md not found")
        content = catalog.read_text()
        # Check for phase references
        for phase_num in range(1, 29):
            assert f'Phase {phase_num}' in content or \
                   f'phase {phase_num}' in content.lower() or \
                   f'phase{phase_num}' in content.lower(), (
                f"Phase {phase_num} not documented in TDD_CATALOG.md"
            )
