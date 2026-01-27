# Test-Driven Development Guide - Chicken Coop Monitoring System

This directory contains a systematic TDD test suite for greenfield development of the chicken coop monitoring system. Tests are organized in phases that build upon each other, following the dependency hierarchy of the system.

## Development Philosophy

**Red-Green-Refactor Cycle:**
1. **Red** - Write a failing test that defines expected behavior
2. **Green** - Write minimal code to make the test pass
3. **Refactor** - Improve code quality while keeping tests green

**Key Principles:**
- Tests define the contract before implementation
- Each phase must pass before moving to the next
- Mock external dependencies (hardware, AWS, network)
- Keep tests fast and isolated

## Phase Overview

```
Phase 1: Foundation          (No dependencies)
    ↓
Phase 2: Hardware            (Depends on Phase 1)
    ↓
Phase 3: Persistence         (Depends on Phase 1, 2)
    ↓
Phase 4: AWS Integration     (Depends on Phase 1, 3)
    ↓
Phase 5: API Layer           (Depends on Phase 1-4)
    ↓
Phase 6: Frontend            (Depends on Phase 5)
    ↓
Phase 7: Integration/E2E     (Depends on all phases)
```

## Directory Structure

```
tdd/
├── README.md                    # This file
├── conftest.py                  # Shared pytest fixtures
├── pytest.ini                   # Pytest configuration
│
├── phase1_foundation/           # Core utilities and configuration
│   ├── config/                  # Configuration loading and validation
│   ├── utils/                   # Helper functions and utilities
│   └── models/                  # Data models and validation
│
├── phase2_hardware/             # Hardware abstraction layer
│   ├── sensors/                 # Temperature, humidity sensors
│   ├── camera/                  # Camera control and recording
│   └── motion/                  # Motion detection algorithms
│
├── phase3_persistence/          # Data storage layer
│   ├── local_db/                # SQLite database operations
│   └── csv_storage/             # CSV file management
│
├── phase4_aws/                  # Cloud integration
│   ├── s3/                      # S3 uploads and downloads
│   ├── iot/                     # IoT Core MQTT messaging
│   ├── sns/                     # Alert notifications
│   └── lambda/                  # Lambda handler patterns
│
├── phase5_api/                  # API layer
│   ├── auth/                    # Authentication and authorization
│   ├── routes/                  # Flask route handlers
│   └── endpoints/               # REST API endpoints
│
├── phase6_frontend/             # React frontend
│   ├── components/              # UI components
│   ├── services/                # API service layer
│   └── pages/                   # Page components
│
└── phase7_integration/          # Integration and E2E tests
    ├── system/                  # Full system integration
    └── e2e/                     # End-to-end user flows
```

## Running Tests

### Run All Tests in Order
```bash
# From repository root
pytest tdd/ -v --tb=short

# Run with coverage
pytest tdd/ -v --cov=src --cov-report=html
```

### Run Specific Phase
```bash
# Phase 1 only (start here for greenfield)
pytest tdd/phase1_foundation/ -v

# Phase 2 after Phase 1 passes
pytest tdd/phase2_hardware/ -v

# Continue through phases...
```

### TDD Workflow
```bash
# 1. Run tests (should fail - RED)
pytest tdd/phase1_foundation/config/test_config_loader.py -v

# 2. Implement minimal code to pass (GREEN)
# ... write implementation ...

# 3. Run tests again (should pass)
pytest tdd/phase1_foundation/config/test_config_loader.py -v

# 4. Refactor if needed, ensure tests still pass
```

## Implementation Order

### Phase 1: Foundation (Week 1)
1. `test_config_loader.py` - Configuration file loading
2. `test_config_validation.py` - Schema validation
3. `test_environment.py` - Environment variable handling
4. `test_logging_setup.py` - Logging configuration
5. `test_path_utils.py` - Path manipulation utilities
6. `test_time_utils.py` - Timestamp handling
7. `test_base_models.py` - Base data model classes
8. `test_sensor_models.py` - Sensor reading models
9. `test_video_models.py` - Video metadata models
10. `test_chicken_models.py` - Chicken registry models

### Phase 2: Hardware (Week 2)
1. `test_sensor_interface.py` - Sensor abstraction
2. `test_temperature_sensor.py` - Temperature reading
3. `test_humidity_sensor.py` - Humidity reading
4. `test_camera_interface.py` - Camera abstraction
5. `test_camera_capture.py` - Image/video capture
6. `test_camera_config.py` - Resolution and settings
7. `test_motion_detector.py` - Motion detection algorithm
8. `test_motion_regions.py` - Region-based detection
9. `test_motion_sensitivity.py` - Threshold tuning

### Phase 3: Persistence (Week 3)
1. `test_database_connection.py` - SQLite connection
2. `test_user_repository.py` - User CRUD operations
3. `test_chicken_repository.py` - Chicken CRUD
4. `test_video_repository.py` - Video metadata CRUD
5. `test_headcount_repository.py` - Headcount logs
6. `test_csv_writer.py` - CSV file writing
7. `test_csv_reader.py` - CSV file reading
8. `test_csv_rotation.py` - Daily file rotation

### Phase 4: AWS Integration (Week 4)
1. `test_s3_client.py` - S3 client wrapper
2. `test_s3_upload.py` - File uploads
3. `test_s3_download.py` - File downloads
4. `test_s3_presigned.py` - Presigned URLs
5. `test_iot_client.py` - IoT Core client
6. `test_iot_publish.py` - MQTT publishing
7. `test_iot_subscribe.py` - MQTT subscription
8. `test_sns_client.py` - SNS client
9. `test_sns_alerts.py` - Alert notifications
10. `test_lambda_handler.py` - Handler patterns

### Phase 5: API Layer (Week 5)
1. `test_password_hashing.py` - Password security
2. `test_session_management.py` - Login sessions
3. `test_login_required.py` - Route protection
4. `test_csrf_protection.py` - CSRF tokens
5. `test_health_routes.py` - Health check endpoints
6. `test_sensor_routes.py` - Sensor data endpoints
7. `test_video_routes.py` - Video management
8. `test_chicken_routes.py` - Chicken registry
9. `test_alert_routes.py` - Alert subscription

### Phase 6: Frontend (Week 6)
1. `test_api_client.py` - API service layer
2. `test_auth_context.py` - Authentication state
3. `test_sensor_chart.py` - Data visualization
4. `test_video_player.py` - Video playback
5. `test_alert_form.py` - Alert subscription
6. `test_dashboard_page.py` - Main dashboard
7. `test_videos_page.py` - Video listing
8. `test_settings_page.py` - Settings management

### Phase 7: Integration (Week 7)
1. `test_sensor_to_cloud.py` - Sensor → S3/IoT flow
2. `test_motion_to_video.py` - Motion → Recording flow
3. `test_alert_pipeline.py` - Alert end-to-end
4. `test_video_lifecycle.py` - Upload → Retention flow
5. `test_user_login_flow.py` - E2E authentication
6. `test_dashboard_data_flow.py` - E2E data display
7. `test_video_playback_flow.py` - E2E video access

## Test Naming Conventions

```python
# Test file naming
test_{feature}_{aspect}.py

# Test function naming
def test_{action}_{expected_outcome}():
def test_{action}_when_{condition}_{expected_outcome}():
def test_{action}_with_{input}_returns_{output}():

# Examples
def test_load_config_returns_valid_dict():
def test_load_config_when_file_missing_raises_error():
def test_parse_temperature_with_celsius_returns_float():
```

## Fixture Patterns

```python
# conftest.py provides shared fixtures

@pytest.fixture
def sample_config():
    """Valid configuration for testing."""
    return {...}

@pytest.fixture
def mock_sensor():
    """Mocked sensor that returns predictable values."""
    return MockSensor(temperature=72.5, humidity=65.0)

@pytest.fixture
def test_database(tmp_path):
    """Temporary SQLite database for testing."""
    db_path = tmp_path / "test.db"
    return create_test_database(db_path)

@pytest.fixture
def mock_s3_client():
    """Mocked S3 client using moto or unittest.mock."""
    with mock_s3():
        yield boto3.client('s3', region_name='us-east-1')
```

## Mocking Strategy

| Dependency | Mock Approach |
|------------|---------------|
| Hardware sensors | Mock I2C interface |
| Camera | Mock Picamera2 class |
| File system | pytest `tmp_path` fixture |
| SQLite | In-memory database |
| AWS S3 | moto library or unittest.mock |
| AWS IoT | unittest.mock |
| AWS SNS | moto library |
| Time/dates | freezegun library |
| Network | responses library |

## Success Criteria

Each phase is complete when:
1. All tests in the phase pass
2. Code coverage exceeds 80%
3. No linting errors (pylint/eslint)
4. Implementation matches test specifications
5. Documentation updated for new features

## Getting Started

1. **Setup test environment:**
   ```bash
   cd chickencoop-monitoring
   python -m venv venv
   source venv/bin/activate
   pip install pytest pytest-cov pytest-mock moto freezegun
   ```

2. **Run Phase 1 tests (they will fail):**
   ```bash
   pytest tdd/phase1_foundation/ -v
   ```

3. **Implement code to make tests pass**

4. **Proceed to next phase when all tests pass**

## Notes for AI Assistants

- Always run existing tests before making changes
- Implement only enough code to pass the current failing test
- Keep the red-green-refactor cycle short
- Update tests if requirements change
- Document any deviations from the test specifications
