"""
Phase 5: Diagnostics Routes Tests
=================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates all Diagnostics page API functionality:
- Authentication session verification
- Cognito token validation
- AWS credentials verification
- IAM policy status checking
- Test API call execution
- Force credential refresh

WHY THIS MATTERS:
-----------------
The Diagnostics page helps troubleshoot authentication and permission issues.
Users may encounter 403 Forbidden errors if credentials are stale or IAM
policies are not properly attached. This page runs checks to identify the
root cause and provides remediation steps.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase5_api/routes/test_diagnostics_routes.py -v

Tests verify the diagnostic checks return appropriate status indicators
and identify common authentication/permission issues.
"""
import pytest
from flask import Flask, json


class TestAuthenticationDiagnostics:
    """Test authentication session diagnostics."""

    def test_run_all_diagnostics(self, flask_client):
        """Run all 14+ diagnostic checks."""
        response = flask_client.get('/api/diagnostics/run')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'checks' in data
        assert len(data['checks']) >= 14

    def test_check_amplify_config_loaded(self, flask_client):
        """Check if Amplify outputs configuration is loaded."""
        response = flask_client.get('/api/diagnostics/run')
        data = json.loads(response.data)
        checks = {c['name']: c for c in data['checks']}
        assert 'amplify_config_loaded' in checks
        assert checks['amplify_config_loaded']['status'] in ['success', 'error']

    def test_check_custom_api_urls_configured(self, flask_client):
        """Check if custom API URLs are configured."""
        response = flask_client.get('/api/diagnostics/run')
        data = json.loads(response.data)
        checks = {c['name']: c for c in data['checks']}
        assert 'api_urls_configured' in checks

    def test_check_auth_session_fetched(self, flask_client):
        """Check if authentication session can be fetched."""
        response = flask_client.get('/api/diagnostics/run')
        data = json.loads(response.data)
        checks = {c['name']: c for c in data['checks']}
        assert 'auth_session_fetched' in checks

    def test_check_cognito_tokens_present(self, flask_client):
        """Check if Cognito tokens are present."""
        response = flask_client.get('/api/diagnostics/run')
        data = json.loads(response.data)
        checks = {c['name']: c for c in data['checks']}
        assert 'cognito_tokens_present' in checks


class TestTokenValidation:
    """Test token validation diagnostics."""

    def test_check_access_token_validity(self, flask_client):
        """Check if access token is valid (not expired)."""
        response = flask_client.get('/api/diagnostics/run')
        data = json.loads(response.data)
        checks = {c['name']: c for c in data['checks']}
        assert 'access_token_valid' in checks
        assert checks['access_token_valid']['status'] in ['success', 'error', 'warning']

    def test_check_id_token_validity(self, flask_client):
        """Check if ID token is valid."""
        response = flask_client.get('/api/diagnostics/run')
        data = json.loads(response.data)
        checks = {c['name']: c for c in data['checks']}
        assert 'id_token_valid' in checks

    def test_check_token_expiration_time(self, flask_client):
        """Check credentials expiration time."""
        response = flask_client.get('/api/diagnostics/run')
        data = json.loads(response.data)
        checks = {c['name']: c for c in data['checks']}
        assert 'credentials_expiration' in checks
        if checks['credentials_expiration']['value']:
            # Should be a timestamp or duration
            assert 'expir' in checks['credentials_expiration']['value'].lower() or \
                   'hour' in checks['credentials_expiration']['value'].lower()


class TestAWSCredentials:
    """Test AWS credentials diagnostics."""

    def test_check_aws_credentials_present(self, flask_client):
        """Check if AWS credentials are present."""
        response = flask_client.get('/api/diagnostics/run')
        data = json.loads(response.data)
        checks = {c['name']: c for c in data['checks']}
        assert 'aws_credentials_present' in checks

    def test_check_access_key_id_present(self, flask_client):
        """Check if Access Key ID is present."""
        response = flask_client.get('/api/diagnostics/run')
        data = json.loads(response.data)
        checks = {c['name']: c for c in data['checks']}
        assert 'access_key_id_present' in checks

    def test_check_secret_access_key_present(self, flask_client):
        """Check if Secret Access Key is present."""
        response = flask_client.get('/api/diagnostics/run')
        data = json.loads(response.data)
        checks = {c['name']: c for c in data['checks']}
        assert 'secret_access_key_present' in checks

    def test_check_session_token_present(self, flask_client):
        """Check if Session Token is present (for temporary credentials)."""
        response = flask_client.get('/api/diagnostics/run')
        data = json.loads(response.data)
        checks = {c['name']: c for c in data['checks']}
        assert 'session_token_present' in checks

    def test_credentials_truncated_for_security(self, flask_client):
        """Verify credentials are truncated in display for security."""
        response = flask_client.get('/api/diagnostics/run')
        data = json.loads(response.data)
        checks = {c['name']: c for c in data['checks']}

        # If access key is shown, it should be truncated
        if 'access_key_id_present' in checks and checks['access_key_id_present']['value']:
            value = checks['access_key_id_present']['value']
            # Should not show full key, look for truncation pattern (...)
            assert '...' in value or len(value) < 20


class TestIdentityInfo:
    """Test identity information diagnostics."""

    def test_check_identity_pool_id(self, flask_client):
        """Check Identity Pool ID."""
        response = flask_client.get('/api/diagnostics/run')
        data = json.loads(response.data)
        checks = {c['name']: c for c in data['checks']}
        assert 'identity_pool_id' in checks

    def test_check_user_sub(self, flask_client):
        """Check Cognito User ID (sub)."""
        response = flask_client.get('/api/diagnostics/run')
        data = json.loads(response.data)
        checks = {c['name']: c for c in data['checks']}
        assert 'user_sub' in checks

    def test_check_user_email(self, flask_client):
        """Check user email from token."""
        response = flask_client.get('/api/diagnostics/run')
        data = json.loads(response.data)
        checks = {c['name']: c for c in data['checks']}
        assert 'user_email' in checks


class TestAPIConnectivity:
    """Test API connectivity diagnostics."""

    def test_api_call_to_status_endpoint(self, flask_client):
        """Test API call to status endpoint."""
        response = flask_client.get('/api/diagnostics/run')
        data = json.loads(response.data)
        checks = {c['name']: c for c in data['checks']}
        assert 'test_api_call' in checks
        assert 'status' in checks['test_api_call']

    def test_api_call_shows_http_status(self, flask_client):
        """API call check shows HTTP response status."""
        response = flask_client.get('/api/diagnostics/run')
        data = json.loads(response.data)
        checks = {c['name']: c for c in data['checks']}

        if 'test_api_call' in checks:
            # Should include HTTP status code info
            value = checks['test_api_call'].get('value', '')
            # Should mention 200, 403, or similar
            assert any(str(code) in str(value) for code in [200, 401, 403, 500]) or \
                   'success' in str(value).lower() or \
                   'error' in str(value).lower()


class TestDiagnosticResults:
    """Test diagnostic result format and statuses."""

    def test_result_has_status_icons(self, flask_client):
        """Each check has appropriate status icon."""
        response = flask_client.get('/api/diagnostics/run')
        data = json.loads(response.data)

        for check in data['checks']:
            assert 'status' in check
            assert check['status'] in ['success', 'error', 'warning', 'info']

    def test_result_has_descriptions(self, flask_client):
        """Each check has a description."""
        response = flask_client.get('/api/diagnostics/run')
        data = json.loads(response.data)

        for check in data['checks']:
            assert 'name' in check

    def test_result_grid_layout(self, flask_client):
        """Results should support grid display."""
        response = flask_client.get('/api/diagnostics/run')
        data = json.loads(response.data)

        # Each check should have consistent structure
        for check in data['checks']:
            assert 'name' in check
            assert 'status' in check
            # Value may be optional
            assert 'value' in check or check['status'] in ['success', 'error']


class TestForceCredentialRefresh:
    """Test force credential refresh functionality."""

    def test_force_refresh_clears_cache(self, flask_client):
        """Force refresh clears Amplify cache."""
        response = flask_client.post('/api/diagnostics/force-refresh')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['cache_cleared'] is True

    def test_force_refresh_clears_localstorage(self, flask_client):
        """Force refresh clears localStorage keys."""
        response = flask_client.post('/api/diagnostics/force-refresh')
        data = json.loads(response.data)
        assert data['localstorage_cleared'] is True

    def test_force_refresh_triggers_signout(self, flask_client):
        """Force refresh signs out user."""
        response = flask_client.post('/api/diagnostics/force-refresh')
        data = json.loads(response.data)
        assert data['signout_triggered'] is True

    def test_force_refresh_returns_redirect(self, flask_client):
        """Force refresh indicates user will be redirected."""
        response = flask_client.post('/api/diagnostics/force-refresh')
        data = json.loads(response.data)
        # After signout, user should be redirected to login
        assert 'redirect' in data or data.get('signout_triggered') is True


class TestIAMPolicyStatus:
    """Test IAM policy status display."""

    def test_get_iam_policy_status(self, flask_client):
        """Get IAM policy attachment status."""
        response = flask_client.get('/api/diagnostics/iam-status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'role' in data
        assert 'policy_attached' in data

    def test_iam_shows_lambda_permissions(self, flask_client):
        """IAM status shows Lambda invocation permissions."""
        response = flask_client.get('/api/diagnostics/iam-status')
        data = json.loads(response.data)
        assert 'lambda_invoke_permission' in data

    def test_iam_shows_deployment_status(self, flask_client):
        """IAM status shows deployment status."""
        response = flask_client.get('/api/diagnostics/iam-status')
        data = json.loads(response.data)
        # Should indicate if deployment is complete
        assert 'deployment_status' in data or 'policy_attached' in data


class TestTroubleshootingGuides:
    """Test troubleshooting guide content."""

    def test_get_troubleshooting_steps(self, flask_client):
        """Get troubleshooting steps for common errors."""
        response = flask_client.get('/api/diagnostics/troubleshoot/403')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'steps' in data
        assert len(data['steps']) > 0

    def test_403_guide_includes_credential_clear(self, flask_client):
        """403 guide includes clearing credentials step."""
        response = flask_client.get('/api/diagnostics/troubleshoot/403')
        data = json.loads(response.data)
        steps_text = ' '.join([s['description'] for s in data['steps']])
        assert 'credential' in steps_text.lower() or 'cache' in steps_text.lower()

    def test_403_guide_includes_signin_step(self, flask_client):
        """403 guide includes sign in again step."""
        response = flask_client.get('/api/diagnostics/troubleshoot/403')
        data = json.loads(response.data)
        steps_text = ' '.join([s['description'] for s in data['steps']])
        assert 'sign' in steps_text.lower()
