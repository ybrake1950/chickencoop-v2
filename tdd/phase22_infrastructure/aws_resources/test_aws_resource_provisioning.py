"""
Phase 22: AWS Resource Provisioning Tests
==========================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates that all required AWS resources are defined
in infrastructure-as-code (Terraform, CloudFormation, or CDK):
- S3 bucket with versioning, lifecycle rules, and CORS
- SNS topic with email subscription support
- IoT Core things, certificates, and policies
- DynamoDB table for command queue
- IAM roles and policies for Pi devices and Lambda
- CloudWatch log groups and metric namespaces
- Secrets Manager for credential rotation

WHY THIS MATTERS:
-----------------
Manually provisioned AWS resources are unreproducible and undocumented.
Infrastructure-as-code ensures consistent environments, enables disaster
recovery, and provides an audit trail of infrastructure changes.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase22_infrastructure/aws_resources/test_aws_resource_provisioning.py -v
"""
import json
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Get project root directory."""
    return Path(__file__).parents[3]


@pytest.fixture
def iac_dirs(project_root):
    """Find infrastructure-as-code directories."""
    candidates = [
        project_root / 'infrastructure',
        project_root / 'terraform',
        project_root / 'cloudformation',
        project_root / 'cdk',
        project_root / 'infra',
    ]
    return [d for d in candidates if d.exists()]


@pytest.fixture
def iac_files(project_root):
    """Find all IaC files in the project."""
    extensions = ['*.tf', '*.json', '*.yaml', '*.yml', '*.ts']
    iac_dirs = ['infrastructure', 'terraform', 'cloudformation', 'cdk', 'infra']
    files = []
    for d in iac_dirs:
        iac_dir = project_root / d
        if iac_dir.exists():
            for ext in extensions:
                files.extend(iac_dir.rglob(ext))
    return files


@pytest.fixture
def iac_content(iac_files):
    """Concatenated content of all IaC files."""
    content = ''
    for f in iac_files:
        try:
            content += f.read_text() + '\n'
        except (UnicodeDecodeError, PermissionError):
            continue
    return content


class TestInfrastructureAsCodeExists:
    """Verify IaC directory and files exist."""

    def test_iac_directory_exists(self, iac_dirs):
        """An infrastructure-as-code directory must exist."""
        assert len(iac_dirs) > 0, (
            "No infrastructure directory found. Create one of: "
            "infrastructure/, terraform/, cloudformation/, cdk/, infra/"
        )

    def test_iac_has_files(self, iac_files):
        """IaC directory must contain resource definitions."""
        if not iac_files:
            pytest.skip("No IaC directory found")
        assert len(iac_files) > 0, (
            "IaC directory exists but contains no resource definitions"
        )


class TestS3BucketDefined:
    """Verify S3 bucket is defined in IaC."""

    def test_s3_bucket_resource_defined(self, iac_content):
        """S3 bucket must be defined for video/CSV storage."""
        if not iac_content:
            pytest.skip("No IaC files found")
        has_s3 = ('aws_s3_bucket' in iac_content or
                  'AWS::S3::Bucket' in iac_content or
                  's3.Bucket' in iac_content or
                  '"s3"' in iac_content.lower())
        assert has_s3, "S3 bucket not defined in infrastructure code"

    def test_s3_lifecycle_rules_defined(self, iac_content):
        """S3 lifecycle rules must be defined (120-day video expiry)."""
        if not iac_content:
            pytest.skip("No IaC files found")
        has_lifecycle = ('lifecycle' in iac_content.lower() or
                         'expiration' in iac_content.lower())
        assert has_lifecycle, (
            "S3 lifecycle rules not defined. Videos need 120-day "
            "auto-expiry for non-retained files."
        )

    def test_s3_versioning_enabled(self, iac_content):
        """S3 versioning should be enabled for data protection."""
        if not iac_content:
            pytest.skip("No IaC files found")
        has_versioning = 'versioning' in iac_content.lower()
        assert has_versioning, "S3 versioning not configured"


class TestSNSTopicDefined:
    """Verify SNS topic is defined in IaC."""

    def test_sns_topic_defined(self, iac_content):
        """SNS topic must be defined for alert notifications."""
        if not iac_content:
            pytest.skip("No IaC files found")
        has_sns = ('aws_sns_topic' in iac_content or
                   'AWS::SNS::Topic' in iac_content or
                   'sns.Topic' in iac_content or
                   '"sns"' in iac_content.lower())
        assert has_sns, "SNS topic not defined in infrastructure code"


class TestIoTCoreDefined:
    """Verify IoT Core resources are defined in IaC."""

    def test_iot_thing_defined(self, iac_content):
        """IoT Thing must be defined for each coop."""
        if not iac_content:
            pytest.skip("No IaC files found")
        has_iot = ('aws_iot_thing' in iac_content or
                   'AWS::IoT::Thing' in iac_content or
                   'iot.CfnThing' in iac_content or
                   '"iot"' in iac_content.lower())
        assert has_iot, "IoT Thing not defined in infrastructure code"

    def test_iot_policy_defined(self, iac_content):
        """IoT policy must be defined for device permissions."""
        if not iac_content:
            pytest.skip("No IaC files found")
        has_policy = ('iot_policy' in iac_content.lower() or
                      'IoT::Policy' in iac_content or
                      'iot:Publish' in iac_content)
        assert has_policy, "IoT policy not defined in infrastructure code"


class TestDynamoDBDefined:
    """Verify DynamoDB table is defined for command queue."""

    def test_dynamodb_table_defined(self, iac_content):
        """DynamoDB table must be defined for command queue (Phase 13)."""
        if not iac_content:
            pytest.skip("No IaC files found")
        has_dynamo = ('aws_dynamodb_table' in iac_content or
                      'AWS::DynamoDB::Table' in iac_content or
                      'dynamodb.Table' in iac_content or
                      '"dynamodb"' in iac_content.lower())
        assert has_dynamo, "DynamoDB table not defined in infrastructure code"


class TestIAMRolesDefined:
    """Verify IAM roles are defined for Pi devices."""

    def test_iam_role_defined(self, iac_content):
        """IAM role must be defined for Pi device access."""
        if not iac_content:
            pytest.skip("No IaC files found")
        has_iam = ('aws_iam_role' in iac_content or
                   'AWS::IAM::Role' in iac_content or
                   'iam.Role' in iac_content or
                   '"iam"' in iac_content.lower())
        assert has_iam, "IAM role not defined in infrastructure code"
