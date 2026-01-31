# Production Deployment TODO

Comprehensive checklist for deploying chickencoop-v2 to production. Items are ordered by priority and dependency.

---

## Current State Summary

- **18 TDD phases completed** with tests written and minimal implementation code
- **1,149 tests passing**, 16 failing, 10 test files cannot collect (missing runtime deps)
- **80 tests skipped** (hardware-dependent, AWS-dependent markers)
- Source code: ~67 Python files in `src/`, ~9,600 lines of implementation
- No production `requirements.txt`, no `main.py` entry point, no webapp directory

---

## PRIORITY 1: Critical Blockers (Application Cannot Start)

### 1.1 Create `requirements.txt` (production dependencies)
- [ ] Create `requirements.txt` with all runtime dependencies discovered in source imports:
  - `flask` (API layer, auth, routes, CSRF)
  - `boto3` (S3, IoT Core, SNS, DynamoDB)
  - `botocore` (AWS error handling)
  - `requests` (webhooks, HTTP clients)
  - `numpy` (motion detection frame processing)
  - `opencv-python-headless` / `cv2` (camera, motion detection, chicken counting)
  - `psutil` (system metrics collection - CPU, memory, disk)
  - Pin versions for reproducibility
- [ ] Verify `pip install -r requirements.txt` succeeds cleanly

### 1.2 Create `src/main.py` entry point
- [ ] Implement Flask application factory
- [ ] Register all route blueprints (sensors, videos, chickens, alerts, admin, diagnostics, headcount, settings, auth, SNS)
- [ ] Initialize AWS clients (S3, IoT, SNS)
- [ ] Initialize database connection and run migrations
- [ ] Configure logging with coop ID
- [ ] Set up CORS, CSRF, security headers
- [ ] Add health check endpoint (`/health`)
- [ ] Add graceful shutdown handler (SIGTERM)
- [ ] Systemd service calls `python -m src.main` — this file MUST exist

### 1.3 Add missing `__init__.py` files
- [ ] `src/hardware/__init__.py`
- [ ] `src/hardware/sensors/__init__.py`
- [ ] `src/hardware/motion/__init__.py`
- [ ] Audit all `src/` subdirectories for missing `__init__.py` files

### 1.4 Create `pyproject.toml` or `setup.py`
- [ ] Define package metadata (name, version, description)
- [ ] Declare dependencies (mirrors requirements.txt)
- [ ] Define entry points (`chickencoop = src.main:main`)
- [ ] Set Python version requirement (`>=3.11`)

---

## PRIORITY 2: Fix Failing Tests (16 failures + 10 collection errors)

### 2.1 Install missing test dependencies
- [ ] Add `flask` to requirements-dev.txt (or rely on requirements.txt)
- [ ] Add `numpy`, `opencv-python-headless`, `psutil` for test collection
- [ ] Re-run full test suite: `pytest tdd/ -v --tb=short`

### 2.2 Fix 12 authentication test failures (Phase 5)
- Tests in `tdd/phase5_api/auth/test_authentication.py` failing because Flask is not installed
- [ ] After installing Flask, re-verify all auth tests pass:
  - `test_hash_password_returns_string`
  - `test_allows_authenticated_request`
  - `test_rejects_unauthenticated_request`
  - `test_generate_csrf_token` / `test_validate_csrf_token`
  - `test_generate_reset_token` / `test_validate_reset_token`
  - `test_expired_reset_token_invalid`

### 2.3 Fix 4 systemd service test failures (Phase 8)
- Tests in `tdd/phase8_devops/services/test_systemd_services.py` expecting:
- [ ] Add `Environment=COOP_ID=%H` (or equivalent) to systemd service file
- [ ] Add `StandardOutput=append:/var/log/chickencoop/stdout.log` (or journal directive)
- [ ] Add `StandardError=append:/var/log/chickencoop/stderr.log` (or journal directive)
- [ ] Add `ExecStartPre` directive for video directory cleanup

### 2.4 Fix sensor interface test failure (Phase 2)
- [ ] Fix `test_temperature_sensor_inherits_interface` — verify TemperatureSensor properly inherits from base Sensor ABC

### 2.5 Fix camera test error (Phase 2)
- [ ] Fix `test_capture_returns_image_array` — likely needs numpy/cv2 installed

### 2.6 Verify all 10 previously uncollectable test files now pass
- [ ] `tdd/phase2_hardware/motion/test_motion_detector.py` (needs cv2/numpy)
- [ ] `tdd/phase5_api/routes/test_admin_routes.py` (needs flask)
- [ ] `tdd/phase5_api/routes/test_alert_routes.py` (needs flask)
- [ ] `tdd/phase5_api/routes/test_diagnostics_routes.py` (needs flask)
- [ ] `tdd/phase5_api/routes/test_headcount_routes.py` (needs flask)
- [ ] `tdd/phase5_api/routes/test_settings_routes.py` (needs flask)
- [ ] `tdd/phase6_frontend/pages/test_dashboard_page.py` (needs flask)
- [ ] `tdd/phase6_frontend/services/test_api_service.py` (needs flask)
- [ ] `tdd/phase16_camera_intelligence/counting/test_chicken_counting.py` (needs cv2/numpy)
- [ ] `tdd/phase18_observability/metrics/test_metrics_collection.py` (needs psutil)

---

## PRIORITY 3: Configuration & Environment Setup

### 3.1 Create `.env.example` template
- [ ] Document all required environment variables:
  ```
  COOP_ID=coop1                    # Required: coop1 or coop2
  SECRET_KEY=<generate-secure-key> # Required in production
  TESTING=false                    # Set to true for test mode
  AWS_REGION=us-east-1             # AWS region
  AWS_ACCESS_KEY_ID=               # Or use IAM role on Pi
  AWS_SECRET_ACCESS_KEY=           # Or use IAM role on Pi
  LOG_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR
  CONFIG_DIR=/home/pi/chickencoop-v2/config
  ```

### 3.2 Fix systemd service file
- **File:** `config/systemd/chickencoop-monitor.service`
- [ ] Fix `WorkingDirectory` path: `/home/pi/chickencoop` → `/home/pi/chickencoop-v2`
- [ ] Add `Environment=COOP_ID=%H` for hostname-based coop detection
- [ ] Add logging directives (StandardOutput/StandardError)
- [ ] Add `ExecStartPre` for cleanup tasks
- [ ] Add `EnvironmentFile=-/home/pi/chickencoop-v2/.env` for secrets

### 3.3 Replace placeholder values in configuration
- [ ] `src/config/aws_config.json`: Replace `your-iot-endpoint.iot.us-east-1.amazonaws.com` with real endpoint
- [ ] `src/config/aws_config.json`: Replace `arn:aws:sns:us-east-1:123456789:alerts` with real ARN
- [ ] `src/config/aws_config.json`: Replace `chickencoop-bucket` with real S3 bucket name
- [ ] Consider loading these from environment variables instead of hardcoded JSON

---

## PRIORITY 4: Infrastructure Provisioning

### 4.1 Create AWS infrastructure (Terraform or CloudFormation)
- [ ] S3 bucket for video and CSV storage
  - Enable versioning
  - Set lifecycle rules (120-day expiry for non-retained videos)
  - Configure CORS for presigned URL access
- [ ] SNS topic for alerts
  - Configure email subscription
- [ ] IoT Core setup
  - Create Thing for each coop
  - Generate device certificates
  - Create IoT policy for pub/sub
  - Configure MQTT endpoint
- [ ] DynamoDB table for command queue (Phase 13)
- [ ] IAM roles and policies
  - Pi device role (S3, IoT, SNS, DynamoDB access)
  - Lambda execution role (if using Lambda)
- [ ] CloudWatch log groups and metric namespaces (Phase 18)
- [ ] X-Ray tracing configuration (Phase 18)
- [ ] Secrets Manager for credential rotation (Phase 10)

### 4.2 Create Lambda backend (if using serverless API)
- [ ] Create `webapp/backend/` directory structure
- [ ] Package Flask app as Lambda function (or create separate Lambda handlers)
- [ ] Configure API Gateway or Lambda Function URLs
- [ ] Set up Cognito user pool for frontend authentication

### 4.3 Create frontend webapp
- [ ] Create `webapp/frontend/` React application
- [ ] Implement dashboard page (Phase 6 tests reference React components)
- [ ] Configure Amplify or S3+CloudFront hosting
- [ ] Set up build pipeline (`npm ci && npm run build`)

---

## PRIORITY 5: Deployment Pipeline Fixes

### 5.1 Fix `deploy.sh` script
- [ ] Correct remote path: `/home/pi/chickencoop-v2` (not `/home/pi/chickencoop`)
- [ ] Add pre-deployment health check
- [ ] Add rollback capability on failed deployment
- [ ] Add `pip install -r requirements.txt` step on each Pi
- [ ] Add virtual environment setup/activation
- [ ] Add deployment logging

### 5.2 Fix `.github/workflows/main.yml`
- [ ] Add `pip install -r requirements.txt` step to CI (currently only installs dev deps)
- [ ] Fix or remove `webapp/frontend/` build step (directory doesn't exist yet)
- [ ] Fix or remove `webapp/backend/` Lambda deploy step
- [ ] Replace placeholder health check URL (`api.chickencoop.example.com/health`)
- [ ] Add test coverage thresholds as CI gates

### 5.3 Fix `scripts/install-services.sh`
- [ ] Update paths to match `chickencoop-v2` directory name
- [ ] Add virtual environment creation step
- [ ] Add dependency installation step
- [ ] Add IoT certificate provisioning or documentation

---

## PRIORITY 6: Security Hardening for Production

### 6.1 Secrets management
- [ ] Generate strong `SECRET_KEY` for Flask sessions
- [ ] Set up AWS IAM roles on Raspberry Pis (avoid static credentials)
- [ ] Provision and install IoT device certificates on each Pi
- [ ] Configure certificate rotation schedule
- [ ] Ensure `.env` is in `.gitignore` (already done)

### 6.2 Network security
- [ ] Configure firewall rules on Raspberry Pis (ufw)
- [ ] Enable HTTPS for local API (self-signed cert or Let's Encrypt)
- [ ] Review CORS configuration for production origins
- [ ] Verify rate limiting is configured for production load
- [ ] Enable SSH key-only authentication (disable password auth)

### 6.3 Audit and compliance
- [ ] Verify audit logging writes to persistent storage
- [ ] Configure log rotation on Raspberry Pis
- [ ] Set up CloudWatch log shipping from Pis
- [ ] Review OWASP top 10 checklist against implementation

---

## PRIORITY 7: Monitoring & Observability Setup

### 7.1 CloudWatch integration
- [ ] Configure CloudWatch agent on Raspberry Pis (or use custom metrics via boto3)
- [ ] Create CloudWatch dashboard for system health
- [ ] Set up CloudWatch alarms for:
  - Pi offline detection
  - High error rate
  - Storage capacity warnings
  - Temperature threshold breaches

### 7.2 Alerting pipeline verification
- [ ] Test SNS email subscription end-to-end
- [ ] Test Slack/Discord webhook notifications (Phase 12)
- [ ] Verify alert aggregation prevents alert storms
- [ ] Test quiet hours routing

---

## PRIORITY 8: Raspberry Pi Device Setup

### 8.1 OS and hardware preparation (per device)
- [ ] Flash Raspberry Pi OS (64-bit recommended)
- [ ] Set hostname (`coop1` or `coop2`)
- [ ] Configure WiFi and static IP
- [ ] Enable I2C interface (for temperature/humidity sensors)
- [ ] Enable camera interface
- [ ] Install Python 3.11+ and pip
- [ ] Install system dependencies: `sudo apt install python3-opencv libatlas-base-dev`

### 8.2 Application installation (per device)
- [ ] Clone repository: `git clone` to `/home/pi/chickencoop-v2`
- [ ] Create virtual environment: `python3 -m venv venv`
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Copy `.env` with device-specific values (COOP_ID, SECRET_KEY)
- [ ] Install IoT certificates to `config/certs/`
- [ ] Run `scripts/install-services.sh`
- [ ] Verify service starts: `sudo systemctl status chickencoop-monitor`
- [ ] Verify sensor readings in logs
- [ ] Verify S3 uploads working
- [ ] Verify IoT Core publishing

---

## PRIORITY 9: Pre-Launch Verification

### 9.1 Full test suite green
- [ ] All tests pass: `pytest tdd/ -v` (target: 0 failures, 0 collection errors)
- [ ] Coverage report: `pytest tdd/ --cov=src --cov-report=html` (target: >80%)
- [ ] Type checking: `mypy src/` passes
- [ ] Linting: `pylint src/ --errors-only` passes
- [ ] Code formatting: `black --check src/` passes

### 9.2 Integration testing
- [ ] Sensor → CSV → S3 pipeline works end-to-end
- [ ] Motion detection → video recording → S3 upload works
- [ ] Temperature threshold → SNS alert delivery works
- [ ] Nightly headcount triggers and reports correctly
- [ ] Dashboard loads and displays real-time data
- [ ] Offline operation: disconnect WiFi, verify local buffering
- [ ] Reconnection: restore WiFi, verify data sync to cloud

### 9.3 Disaster recovery testing
- [ ] Simulate power loss: unplug Pi, verify clean recovery
- [ ] Simulate SD card failure: restore from backup
- [ ] Verify configuration rollback works
- [ ] Test cross-coop failover notification

---

## PRIORITY 10: Documentation

### 10.1 Operations documentation
- [ ] Deployment runbook (step-by-step production deployment)
- [ ] Troubleshooting guide (common issues and fixes)
- [ ] Monitoring guide (what to watch, how to respond)
- [ ] Backup and restore procedures

### 10.2 Architecture documentation
- [ ] System architecture diagram (Pi ↔ AWS ↔ Frontend)
- [ ] Data flow diagram (sensor reading lifecycle)
- [ ] Network diagram (Pi WiFi, AWS services, user access)

---

## TDD Process Verification (per PHASE1_QUICKSTART.md)

The TDD cycle (Red → Green → Refactor) has been followed for all 18 phases. Current status:

| Phase | Tests Written | Impl Written | Tests Passing | Refactored |
|-------|:---:|:---:|:---:|:---:|
| 1. Foundation | ✅ | ✅ | ✅ | ⚠️ Review |
| 2. Hardware Abstraction | ✅ | ✅ | ⚠️ 1 fail + 1 error (missing deps) | ⚠️ Review |
| 3. Data Persistence | ✅ | ✅ | ✅ | ⚠️ Review |
| 4. AWS Integration | ✅ | ✅ | ✅ | ⚠️ Review |
| 5. API Layer | ✅ | ✅ | ⚠️ 12 fail + 5 uncollectable (missing flask) | ⚠️ Review |
| 6. Frontend | ✅ | ✅ | ⚠️ 2 uncollectable (missing flask) | ⚠️ Review |
| 7. Integration & E2E | ✅ | ✅ | ✅ | ⚠️ Review |
| 8. DevOps & CI/CD | ✅ | ✅ | ⚠️ 4 fail (systemd config gaps) | ⚠️ Review |
| 9. Edge Resilience | ✅ | ✅ | ✅ | ⚠️ Review |
| 10. Security Hardening | ✅ | ✅ | ✅ | ⚠️ Review |
| 11. Code Quality | ✅ | ✅ | ✅ | ⚠️ Review |
| 12. Advanced Alerting | ✅ | ✅ | ✅ | ⚠️ Review |
| 13. Command Queue | ✅ | ✅ | ✅ | ⚠️ Review |
| 14. RBAC | ✅ | ✅ | ✅ | ⚠️ Review |
| 15. Real-Time Streaming | ✅ | ✅ | ✅ | ⚠️ Review |
| 16. Camera Intelligence | ✅ | ✅ | ⚠️ 1 uncollectable (missing cv2) | ⚠️ Review |
| 17. Backup & DR | ✅ | ✅ | ✅ | ⚠️ Review |
| 18. Observability | ✅ | ✅ | ⚠️ 1 uncollectable (missing psutil) | ⚠️ Review |

**Key TDD gap:** The "Refactor" step appears incomplete across all phases. Per PHASE1_QUICKSTART.md, the cycle is Red → Green → **Refactor**. Minimal code was written to pass tests, but the refactoring step (improve code quality while keeping tests green) should be verified for each phase before production.

**Specific TDD concerns:**
1. Missing `requirements.txt` means the Green step is incomplete — tests cannot all run in a clean environment
2. 16 test failures and 10 collection errors indicate some implementations are incomplete or dependencies are missing
3. The PHASE1_QUICKSTART.md success criteria of ">80% coverage" and "no linting errors" should be verified
