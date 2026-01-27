# TDD Test Catalog - Complete Functionality Reference

This document provides a comprehensive catalog of all TDD test scripts, describing:
- **What** functionality is being tested
- **How** each test is executed
- **Why** the functionality matters to the system

---

## Table of Contents

1. [Phase 1: Foundation](#phase-1-foundation)
2. [Phase 2: Hardware Abstraction](#phase-2-hardware-abstraction)
3. [Phase 3: Data Persistence](#phase-3-data-persistence)
4. [Phase 4: AWS Integration](#phase-4-aws-integration)
5. [Phase 5: API Layer](#phase-5-api-layer)
6. [Phase 6: Frontend](#phase-6-frontend)
7. [Phase 7: Integration & E2E](#phase-7-integration--e2e)
8. [Phase 8: DevOps & CI/CD](#phase-8-devops--cicd)
9. [Phase 9: Edge Resilience & Offline Operation](#phase-9-edge-resilience--offline-operation)
10. [Phase 10: Security Hardening](#phase-10-security-hardening)
11. [Phase 11: Code Quality & Modularity](#phase-11-code-quality--modularity)
12. [Phase 12: Advanced Alerting](#phase-12-advanced-alerting)
13. [Phase 13: Command Queue](#phase-13-command-queue)
14. [Phase 14: Role-Based Access Control](#phase-14-role-based-access-control)
15. [Phase 15: Real-Time Streaming](#phase-15-real-time-streaming)
16. [Phase 16: Multi-Camera Intelligence](#phase-16-multi-camera-intelligence)
17. [Phase 17: Backup & Disaster Recovery](#phase-17-backup--disaster-recovery)
18. [Phase 18: Performance & Observability](#phase-18-performance--observability)
19. [Functionality Coverage Matrix](#functionality-coverage-matrix)

---

## Phase 1: Foundation

Phase 1 establishes the core building blocks with **zero external dependencies**. All other phases build upon these foundational components.

### 1.1 Configuration Loader (`test_config_loader.py`)

**Functionality Being Tested:**
- Loading JSON configuration files from disk
- Handling missing or malformed configuration files
- Merging base configuration with device-specific overrides
- Resolving configuration file paths based on environment

**Why This Matters:**
The chicken coop system uses a layered configuration approach where base settings can be overridden per-device (coop1 vs coop2). This allows the same codebase to run on different Raspberry Pi models with different capabilities.

**How Tests Are Executed:**

```bash
# Run all configuration loader tests
pytest tdd/phase1_foundation/config/test_config_loader.py -v

# Run a specific test
pytest tdd/phase1_foundation/config/test_config_loader.py::TestConfigLoader::test_load_config_returns_dict -v
```

**Test Execution Flow:**
1. Tests use the `config_file` fixture from `conftest.py` which creates a temporary JSON file
2. Each test calls functions from `src/config/loader.py`
3. Assertions verify return types, content, and error handling
4. Temporary files are automatically cleaned up after each test

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_load_config_returns_dict` | Verify JSON is parsed into Python dictionary |
| `test_load_config_with_nonexistent_file_raises_error` | Ensure graceful failure for missing files |
| `test_merge_configs_deep_merge_nested_dicts` | Verify device configs override base configs correctly |
| `test_get_device_config_path_uses_coop_id` | Ensure COOP_ID environment variable selects correct config |

---

### 1.2 Configuration Validation (`test_config_validation.py`)

**Functionality Being Tested:**
- Validating configuration schema structure
- Enforcing value constraints (thresholds, ranges)
- Validating sensor configuration parameters
- Validating camera configuration parameters
- Validating AWS configuration format

**Why This Matters:**
Invalid configuration can cause runtime failures in production. Validation catches configuration errors early, before they cause sensor misreadings, camera failures, or AWS connection issues.

**How Tests Are Executed:**

```bash
pytest tdd/phase1_foundation/config/test_config_validation.py -v
```

**Test Execution Flow:**
1. Tests use `sample_config` fixture providing valid configuration
2. Tests modify specific values to test validation rules
3. `ConfigValidationError` exceptions are expected for invalid values
4. Valid configurations should return `True` without exceptions

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_validate_config_rejects_empty_dict` | Ensure empty config fails validation |
| `test_validate_temperature_thresholds_are_valid` | Verify min < max constraint |
| `test_validate_humidity_thresholds_in_valid_range` | Verify 0-100 range for humidity |
| `test_validate_rotation_in_valid_values` | Ensure rotation is 0/90/180/270 only |
| `test_validate_sns_topic_arn_format` | Validate AWS ARN format |

---

### 1.3 Environment Variables (`test_environment.py`)

**Functionality Being Tested:**
- Reading environment variables with type conversion
- Providing default values for missing variables
- Handling required variables in production vs testing modes
- Managing secrets (SECRET_KEY) safely
- Detecting testing vs production environment

**Why This Matters:**
Environment variables control deployment-specific settings like coop identity, AWS region, and secrets. Proper handling ensures the system works correctly across development, testing, and production environments.

**How Tests Are Executed:**

```bash
pytest tdd/phase1_foundation/config/test_environment.py -v
```

**Test Execution Flow:**
1. Tests use `monkeypatch` fixture to safely set/unset environment variables
2. `clean_env` fixture ensures tests start with clean environment state
3. Each test sets specific variables and verifies function behavior
4. Environment is restored after each test

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_get_env_required_raises_when_not_set` | Ensure required variables cause errors if missing |
| `test_get_env_bool_returns_true_for_truthy` | Verify "true", "1", "yes" all work |
| `test_get_coop_id_normalizes_to_lowercase` | Ensure consistent coop ID format |
| `test_get_secret_key_raises_in_production_when_not_set` | Enforce security in production |
| `test_is_testing_returns_true_when_set` | Verify test mode detection |

---

### 1.4 Logging Setup (`test_logging_setup.py`)

**Functionality Being Tested:**
- Creating configured logger instances
- Setting log levels from environment or parameters
- Formatting log messages with timestamps and context
- Writing logs to files with rotation
- Including coop ID in log messages for multi-coop setups

**Why This Matters:**
Proper logging is essential for debugging issues across multiple Raspberry Pis. Each coop needs identifiable logs, and file rotation prevents disk space exhaustion.

**How Tests Are Executed:**

```bash
pytest tdd/phase1_foundation/utils/test_logging_setup.py -v
```

**Test Execution Flow:**
1. Tests create logger instances and capture output
2. `caplog` fixture captures log records for assertion
3. `tmp_path` fixture provides temporary directory for log files
4. Tests verify log format, levels, and file creation

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_get_logger_returns_logger_instance` | Verify logger creation |
| `test_setup_logging_respects_level_parameter` | Verify log level configuration |
| `test_log_messages_written_to_file` | Verify file output works |
| `test_log_file_rotation_by_size` | Verify rotation prevents disk fill |
| `test_log_format_includes_coop_id` | Verify multi-coop log identification |

---

### 1.5 Path Utilities (`test_path_utils.py`)

**Functionality Being Tested:**
- Resolving project root directory
- Getting standard directory paths (config, data, logs)
- Creating directories safely
- Generating video file paths with timestamps
- Generating CSV file paths with dates
- Creating S3 object keys with coop prefixes
- Sanitizing filenames for safety

**Why This Matters:**
Consistent path handling prevents file organization issues across different environments. S3 keys must include coop IDs to keep data separated.

**How Tests Are Executed:**

```bash
pytest tdd/phase1_foundation/utils/test_path_utils.py -v
```

**Test Execution Flow:**
1. Tests use `tmp_path` fixture for temporary directories
2. Path functions are called with various inputs
3. Assertions verify path structure and components
4. File system operations are tested with real temp directories

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_get_project_root_contains_marker_file` | Verify project root detection |
| `test_ensure_dir_creates_nested_directories` | Verify recursive directory creation |
| `test_get_video_path_includes_date` | Verify video filename format |
| `test_get_s3_video_key_includes_coop_id` | Verify S3 key structure for multi-coop |
| `test_sanitize_filename_removes_special_chars` | Prevent filesystem issues |

---

### 1.6 Time Utilities (`test_time_utils.py`)

**Functionality Being Tested:**
- Generating UTC timestamps
- Converting between ISO 8601 format and datetime objects
- Formatting timestamps for filenames and display
- Calculating time ranges (start/end of day, last N days)
- Converting between timezones
- Parsing scheduled times (for headcount scheduling)
- Calculating time differences

**Why This Matters:**
All timestamps in the system use UTC for consistency across timezones. Scheduled tasks like nightly headcount depend on accurate time parsing.

**How Tests Are Executed:**

```bash
pytest tdd/phase1_foundation/utils/test_time_utils.py -v
```

**Test Execution Flow:**
1. Tests create datetime objects with known values
2. Conversion functions are called and results verified
3. `freeze_time` fixture can lock time for deterministic tests
4. Timezone-aware assertions ensure UTC handling

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_now_utc_is_utc_timezone` | Ensure all timestamps are UTC |
| `test_roundtrip_iso_format` | Verify serialization preserves data |
| `test_format_timestamp_for_filename` | Ensure safe filename characters |
| `test_parse_schedule_time_returns_time` | Parse "19:00" format for headcount |
| `test_to_utc_from_aware` | Convert local time to UTC correctly |

---

### 1.7 Base Models (`test_base_models.py`)

**Functionality Being Tested:**
- Base model class with automatic timestamps
- Serialization to dictionary and JSON
- Deserialization from dictionary and JSON
- Model validation framework
- Equality comparison between models
- Model hashing for use in collections
- Creating model copies

**Why This Matters:**
All data models (sensors, videos, chickens) inherit from BaseModel. This ensures consistent serialization for API responses and database storage.

**How Tests Are Executed:**

```bash
pytest tdd/phase1_foundation/models/test_base_models.py -v
```

**Test Execution Flow:**
1. Tests instantiate BaseModel directly
2. Serialization methods are called and JSON validity checked
3. Deserialization creates new instances from serialized data
4. Equality and hash tests ensure collection compatibility

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_base_model_has_created_at` | Verify automatic timestamp |
| `test_base_model_to_dict_returns_dict` | Verify serialization |
| `test_serialization_roundtrip` | Verify data preservation |
| `test_models_with_same_data_are_equal` | Enable model comparison |
| `test_modifying_copy_does_not_affect_original` | Ensure safe copying |

---

### 1.8 Sensor Models (`test_sensor_models.py`)

**Functionality Being Tested:**
- SensorReading model with temperature, humidity, coop_id
- Type validation for numeric fields
- Value range validation (humidity 0-100)
- Anomaly detection for extreme values
- Temperature unit conversion (Fahrenheit ↔ Celsius)
- CSV serialization/deserialization
- SensorReadingBatch for aggregate statistics

**Why This Matters:**
Sensor readings are the core data of the monitoring system. They flow from Pi sensors → local storage → S3 → IoT Core → dashboard. Consistent modeling ensures data integrity throughout.

**How Tests Are Executed:**

```bash
pytest tdd/phase1_foundation/models/test_sensor_models.py -v
```

**Test Execution Flow:**
1. Tests create SensorReading instances with various inputs
2. Validation is triggered explicitly or through property access
3. CSV methods convert to/from row format
4. Batch calculations are verified with known input sets

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_sensor_reading_timestamp_is_utc` | Ensure UTC consistency |
| `test_humidity_must_be_in_range` | Prevent invalid data |
| `test_temperature_sensor_returns_fahrenheit_by_default` | Verify default unit |
| `test_to_csv_row_returns_list` | Enable CSV export |
| `test_batch_average_temperature` | Calculate statistics |

---

### 1.9 Video Models (`test_video_models.py`)

**Functionality Being Tested:**
- VideoMetadata model with filename, S3 key, camera source
- Camera validation (indoor/outdoor only)
- Video retention marking and removal
- Expiration calculation (120-day lifecycle)
- File size formatting for display
- Duration formatting for display
- Thumbnail S3 key generation
- VideoList filtering and sorting

**Why This Matters:**
Videos are stored in S3 with 120-day auto-deletion. Users can mark videos for permanent retention. The video model tracks all metadata for the dashboard.

**How Tests Are Executed:**

```bash
pytest tdd/phase1_foundation/models/test_video_models.py -v
```

**Test Execution Flow:**
1. Tests create VideoMetadata with various attributes
2. Retention methods modify internal state
3. Expiration checks use datetime arithmetic
4. VideoList tests verify filtering and aggregation

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_video_camera_must_be_valid` | Enforce indoor/outdoor only |
| `test_mark_for_retention` | Enable permanent video storage |
| `test_is_expired_without_retention` | Calculate 120-day expiry |
| `test_not_expired_when_retained` | Retained videos never expire |
| `test_filter_by_camera` | Filter videos by source |

---

### 1.10 Chicken Models (`test_chicken_models.py`)

**Functionality Being Tested:**
- Chicken model with name, breed, color, notes
- Active/inactive status for chicken registry
- Color and size profiles for future ML identification
- HeadcountLog model with count, expected, confidence
- All-present calculation
- Counting method tracking (simple_count, ml_detect, manual)
- ChickenRegistry collection operations

**Why This Matters:**
The chicken registry tracks all chickens in each coop. Nightly headcount compares detected count to registered count. Missing chickens trigger SNS alerts.

**How Tests Are Executed:**

```bash
pytest tdd/phase1_foundation/models/test_chicken_models.py -v
```

**Test Execution Flow:**
1. Tests create Chicken instances with profile data
2. HeadcountLog tests verify count calculations
3. Registry tests verify collection operations
4. Active/inactive filtering is verified

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_chicken_is_active_by_default` | New chickens are active |
| `test_all_present_calculated` | Compare detected vs expected |
| `test_headcount_has_confidence` | Track detection confidence |
| `test_get_active_chickens` | Filter out inactive chickens |
| `test_expected_count` | Calculate expected count for alerts |

---

## Phase 2: Hardware Abstraction

Phase 2 creates hardware abstraction layers that work with **mocked hardware** in tests but real hardware in production.

### 2.1 Sensor Interface (`test_sensor_interface.py`)

**Functionality Being Tested:**
- Base Sensor interface with read() method
- TemperatureSensor implementation
- HumiditySensor implementation
- CombinedSensor (temperature + humidity)
- SensorMonitor for managing multiple sensors
- Sensor read failure handling
- Spike detection for anomalous readings

**Why This Matters:**
Sensor abstraction allows testing without physical hardware. The same interface works with real I2C sensors on the Pi and mock sensors in tests.

**How Tests Are Executed:**

```bash
pytest tdd/phase2_hardware/sensors/test_sensor_interface.py -v
```

**Test Execution Flow:**
1. Tests use `mock_i2c_bus` fixture to simulate I2C communication
2. `mock_temperature_sensor` fixture returns predictable values
3. Sensor classes are instantiated with mocked hardware
4. Read operations return expected mock values

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_sensor_has_read_method` | Enforce interface contract |
| `test_temperature_sensor_read_returns_float` | Verify return type |
| `test_combined_sensor_reads_both` | Verify combined operation |
| `test_monitor_handles_sensor_failure` | Graceful degradation |
| `test_detect_temperature_spike` | Alert on rapid changes |

---

### 2.2 Camera Interface (`test_camera_interface.py`)

**Functionality Being Tested:**
- Base Camera interface (capture, start_recording, stop_recording)
- PiCamera implementation wrapping Picamera2
- Resolution and framerate configuration
- Image capture to array or file
- Video recording with start/stop control
- Recording with duration limit
- Camera state management (started, stopped, recording)
- Context manager support for automatic cleanup

**Why This Matters:**
Camera abstraction enables testing video recording logic without physical cameras. The interface handles both indoor Pi Camera and outdoor USB cameras.

**How Tests Are Executed:**

```bash
pytest tdd/phase2_hardware/camera/test_camera_interface.py -v
```

**Test Execution Flow:**
1. Tests use `mock_camera` fixture simulating Picamera2
2. Camera operations are called and mock interactions verified
3. `tmp_path` fixture provides temporary directory for video files
4. State transitions (start → recording → stop) are verified

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_picamera_custom_resolution` | Verify config applied |
| `test_capture_returns_image_array` | Verify capture output |
| `test_start_recording_creates_file` | Verify video creation |
| `test_cannot_start_recording_twice` | Prevent state errors |
| `test_camera_context_manager` | Automatic resource cleanup |

---

### 2.3 Motion Detector (`test_motion_detector.py`)

**Functionality Being Tested:**
- Motion detection using frame differencing
- Sensitivity configuration (0-100 scale)
- Minimum area threshold for noise filtering
- Reference frame management
- Detailed detection results (contours, bounding boxes)
- Region-based detection (limit detection area)
- Auto-update of reference frame

**Why This Matters:**
Motion detection triggers video recording. Proper tuning prevents false positives (recording nothing) and false negatives (missing actual motion).

**How Tests Are Executed:**

```bash
pytest tdd/phase2_hardware/motion/test_motion_detector.py -v
```

**Test Execution Flow:**
1. Tests use `blank_frame` and `frame_with_motion` fixtures (numpy arrays)
2. Detector is configured with sensitivity and min_area
3. Reference frame is set, then test frame is compared
4. Detection results are verified against expected outcomes

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_no_motion_on_identical_frames` | Verify baseline works |
| `test_motion_on_different_frames` | Verify detection works |
| `test_motion_respects_min_area` | Filter small noise |
| `test_details_include_bounding_boxes` | Enable visual debugging |
| `test_motion_only_in_region` | Limit detection area |

---

## Phase 3: Data Persistence

Phase 3 handles local data storage using **SQLite and CSV files**.

### 3.1 Database Connection (`test_database_connection.py`)

**Functionality Being Tested:**
- SQLite database connection and lifecycle
- Database file creation
- Schema migration (create all tables)
- User repository (CRUD operations)
- Password hashing and verification
- Context manager for connection handling
- In-memory database for testing

**Why This Matters:**
Local SQLite stores users, chickens, videos, and headcount logs. This data persists across Pi reboots and syncs to the cloud periodically.

**How Tests Are Executed:**

```bash
pytest tdd/phase3_persistence/local_db/test_database_connection.py -v
```

**Test Execution Flow:**
1. Tests use `test_db_path` fixture for temporary database file
2. Database class creates connection and schema
3. Repository classes perform CRUD operations
4. Password hashing is verified with known inputs

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_create_connection` | Verify database opens |
| `test_create_all_tables` | Verify schema creation |
| `test_create_user` | Verify user insertion |
| `test_verify_password` | Verify password checking |
| `test_context_manager` | Verify automatic cleanup |

---

## Phase 4: AWS Integration

Phase 4 integrates with AWS services using **mocked AWS clients** in tests.

### 4.1 S3 Client (`test_s3_client.py`)

**Functionality Being Tested:**
- S3 client initialization with configuration
- File upload to S3
- File download from S3
- Presigned URL generation with expiry
- Object listing with prefix filtering
- Single and bulk object deletion
- Error handling for missing objects

**Why This Matters:**
S3 stores all videos and CSV sensor data. Presigned URLs allow secure video playback in the dashboard without exposing AWS credentials.

**How Tests Are Executed:**

```bash
pytest tdd/phase4_aws/s3/test_s3_client.py -v
```

**Test Execution Flow:**
1. Tests use `mock_s3_client` fixture from conftest.py
2. boto3.client is patched to return mock
3. S3 operations are called and mock interactions verified
4. `tmp_path` provides temporary files for upload tests

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_upload_file` | Verify file upload works |
| `test_generate_presigned_url` | Enable secure video access |
| `test_presigned_url_expiry` | Verify expiry configuration |
| `test_list_videos` | Get video list for dashboard |
| `test_download_nonexistent_raises` | Handle missing files |

---

## Phase 5: API Layer

Phase 5 implements the Flask API with **authentication and route handling**.

### 5.1 Authentication (`test_authentication.py`)

**Functionality Being Tested:**
- Password hashing with secure algorithm
- Password verification
- Session creation and management
- Session invalidation (logout)
- Login required decorator
- CSRF token generation and validation
- Password reset token generation and validation

**Why This Matters:**
Authentication protects the dashboard from unauthorized access. CSRF protection prevents cross-site request forgery attacks.

**How Tests Are Executed:**

```bash
pytest tdd/phase5_api/auth/test_authentication.py -v
```

**Test Execution Flow:**
1. Tests use `flask_app` and `flask_client` fixtures
2. Password functions are tested with known inputs
3. Session tests manipulate Flask session data
4. CSRF tests verify token lifecycle

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_hash_password_not_plaintext` | Verify secure hashing |
| `test_verify_correct_password` | Verify password checking |
| `test_allows_authenticated_request` | Verify auth flow |
| `test_rejects_unauthenticated_request` | Verify protection |
| `test_validate_csrf_token` | Verify CSRF protection |

---

### 5.2 Sensor Routes (`test_sensor_routes.py`)

**Functionality Being Tested:**
- GET /api/status - System status endpoint
- GET /api/sensor-data - Sensor reading history
- GET /api/alerts - Active alerts
- GET /api/download-csv - CSV data download
- Time range filtering
- Coop ID filtering
- Response format validation

**Why This Matters:**
API routes serve data to the React dashboard. Proper response formats ensure the frontend can display sensor charts and status correctly.

**How Tests Are Executed:**

```bash
pytest tdd/phase5_api/routes/test_sensor_routes.py -v
```

**Test Execution Flow:**
1. Tests register routes with Flask test app
2. Flask test client makes HTTP requests
3. Response status codes and JSON structure verified
4. Authentication is simulated via session

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_status_returns_200` | Verify endpoint works |
| `test_status_contains_temperature` | Verify response content |
| `test_sensor_data_with_time_range` | Verify filtering |
| `test_csv_has_correct_content_type` | Verify file download |

---

## Phase 7: Integration & E2E

Phase 7 tests **complete system flows** across multiple components.

### 7.1 Sensor to Cloud (`test_sensor_to_cloud.py`)

**Functionality Being Tested:**
- Sensor reading → CSV storage flow
- Sensor reading → SQLite storage flow
- Sensor reading → IoT Core publish flow
- Sensor reading → S3 backup flow
- Alert generation for threshold violations
- Complete sensor pipeline end-to-end

**Why This Matters:**
Integration tests verify that all components work together correctly. A sensor reading should flow through storage, IoT, and alert systems.

**How Tests Are Executed:**

```bash
pytest tdd/phase7_integration/system/test_sensor_to_cloud.py -v
```

**Test Execution Flow:**
1. Tests configure all mocked components
2. Sensor service processes a reading
3. Verification that all systems received data
4. Alert verification for threshold violations

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_sensor_reading_saved_to_csv` | Verify local storage |
| `test_sensor_reading_published_to_iot` | Verify cloud publish |
| `test_high_temperature_triggers_alert` | Verify alert system |
| `test_complete_sensor_pipeline` | Verify full flow |

---

### 7.2 User Flows (`test_user_flows.py`)

**Functionality Being Tested:**
- Complete login → dashboard flow
- Logout and session clearing
- Password reset flow
- Video viewing and retention
- Chicken registration and management
- Alert subscription
- Headcount viewing and manual trigger

**Why This Matters:**
E2E tests verify the complete user experience. They catch issues that unit tests miss, like navigation problems or data display errors.

**How Tests Are Executed:**

```bash
pytest tdd/phase7_integration/e2e/test_user_flows.py -v
```

**Test Execution Flow:**
1. Tests simulate complete user journeys
2. Multiple HTTP requests in sequence
3. Session state maintained across requests
4. Final state verified

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_user_can_login_and_access_dashboard` | Verify auth flow |
| `test_user_can_view_video_list` | Verify video access |
| `test_user_can_register_chicken` | Verify registry |
| `test_user_can_subscribe_to_alerts` | Verify SNS flow |
| `test_user_can_trigger_manual_headcount` | Verify headcount |

---

## Phase 5 (Continued): Additional API Routes

### 5.3 Settings Routes (`test_settings_routes.py`)

**Functionality Being Tested:**
- Temperature unit preference (Fahrenheit/Celsius)
- Alert threshold configuration (temp min/max, humidity min/max)
- Notification preferences (email alerts, individual alert types)
- Reset to defaults functionality

**Why This Matters:**
Settings control how the system behaves for each user. Alert thresholds determine when SNS notifications are triggered. Temperature unit preference affects all temperature displays in the dashboard.

**How Tests Are Executed:**

```bash
pytest tdd/phase5_api/routes/test_settings_routes.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_get_temperature_unit_returns_default_fahrenheit` | Verify default unit |
| `test_set_temperature_unit_to_celsius` | Allow unit change |
| `test_min_must_be_less_than_max_temperature` | Validate threshold logic |
| `test_reset_all_settings_to_defaults` | Reset functionality |

---

### 5.4 Admin Routes (`test_admin_routes.py`)

**Functionality Being Tested:**
- Health metrics (Pi memory, storage, S3, AWS billing)
- Camera settings (indoor/outdoor toggles, motion recording)
- Nightly headcount settings
- Timezone configuration
- Dangerous operations (delete all videos, delete sensor data)
- Remote Pi control scripts

**Why This Matters:**
The Admin page provides system management capabilities. Health metrics help identify resource issues. Dangerous operations must be protected with confirmations.

**How Tests Are Executed:**

```bash
pytest tdd/phase5_api/routes/test_admin_routes.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_get_pi_memory_metrics` | Monitor Pi resources |
| `test_delete_all_videos_requires_confirmation` | Prevent accidental deletion |
| `test_system_restart` | Remote Pi control |
| `test_fan_on` | Climate control |

---

### 5.5 Diagnostics Routes (`test_diagnostics_routes.py`)

**Functionality Being Tested:**
- Authentication session verification
- Cognito token validation
- AWS credentials verification
- IAM policy status checking
- Force credential refresh

**Why This Matters:**
The Diagnostics page helps troubleshoot authentication and permission issues. Users may encounter 403 Forbidden errors if credentials are stale.

**How Tests Are Executed:**

```bash
pytest tdd/phase5_api/routes/test_diagnostics_routes.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_run_all_diagnostics` | Run 14+ checks |
| `test_check_access_token_validity` | Token validation |
| `test_force_refresh_clears_cache` | Credential refresh |
| `test_get_iam_policy_status` | Permission check |

---

### 5.6 Headcount Routes (`test_headcount_routes.py`)

**Functionality Being Tested:**
- Latest headcount display (detected vs expected, confidence)
- Headcount statistics (success rate, streak)
- Historical headcount log (last 30 records)
- Manual headcount trigger
- Headcount chart data

**Why This Matters:**
Nightly headcount is a core safety feature verifying all chickens are inside before nightfall. Missing chickens trigger alerts.

**How Tests Are Executed:**

```bash
pytest tdd/phase5_api/routes/test_headcount_routes.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_get_latest_headcount` | Current status |
| `test_get_headcount_stats` | Overall statistics |
| `test_trigger_manual_headcount` | Manual check |
| `test_history_sorted_by_date_descending` | Log ordering |

---

### 5.7 Alert Routes (`test_alert_routes.py`)

**Functionality Being Tested:**
- Alert types overview
- Email subscription management
- Subscription confirmation workflow
- Test alert sending
- Alert history with filtering

**Why This Matters:**
Alerts are the primary notification system. Temperature extremes can harm chickens. The subscription system uses AWS SNS with email confirmation.

**How Tests Are Executed:**

```bash
pytest tdd/phase5_api/routes/test_alert_routes.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_get_alert_types` | Available alert types |
| `test_subscribe_to_alerts` | Email subscription |
| `test_send_test_alert` | Verify delivery |
| `test_get_alert_history` | Historical alerts |

---

## Phase 6: Frontend Components

Phase 6 tests the React frontend components and services.

### 6.1 Dashboard Page (`test_dashboard_page.py`)

**Functionality Being Tested:**
- Coop selection toggle (Coop 1, Coop 2, or both)
- Manual refresh controls and auto-refresh status
- System status display (online/offline, temp, humidity, door)
- Live camera streaming (30-second duration)
- Sensor data charts with time range selection
- Video grid with filters and infinite scroll
- Data export to CSV

**Why This Matters:**
The Dashboard is the main view users see daily. It provides at-a-glance status, real-time sensor readings, live camera feeds, and recent videos.

**How Tests Are Executed:**

```bash
# Backend API tests
pytest tdd/phase6_frontend/pages/test_dashboard_page.py -v

# React component tests
cd webapp && npm test -- Dashboard
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_get_status_for_single_coop` | Coop filtering |
| `test_get_temperature_reading` | Sensor display |
| `test_check_door_endpoint` | Door status |
| `test_chart_time_range_24h` | Time selection |
| `test_video_filter_by_camera` | Video filtering |
| `test_manual_record_button` | Video recording |

---

### 6.2 API Service (`test_api_service.py`)

**Functionality Being Tested:**
- API client initialization with base URL
- Request authentication (Cognito tokens)
- Error handling and retries
- Response transformation
- Request caching

**Why This Matters:**
The API service is the bridge between React components and Lambda backends. Proper authentication ensures secure access.

**How Tests Are Executed:**

```bash
cd webapp && npm test -- api.service
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_authenticated_request_succeeds` | Auth flow |
| `test_404_error_handling` | Error handling |
| `test_status_cached_briefly` | Performance |

---

### 6.3 IoT WebSocket Service (`test_iot_websocket.py`)

**Functionality Being Tested:**
- WebSocket connection to AWS IoT Core
- MQTT topic subscription
- Real-time sensor data updates
- Connection state management
- Reconnection logic

**Why This Matters:**
The IoT WebSocket provides real-time updates without polling. When a Pi publishes readings, the dashboard updates immediately.

**How Tests Are Executed:**

```bash
cd webapp && npm test -- iot
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_receive_temperature_update` | Real-time data |
| `test_reconnect_on_disconnect` | Connection resilience |
| `test_parse_json_message` | Message handling |

---

## Functionality Coverage Matrix

This matrix maps **all application pages** to test coverage:

### Dashboard Page Features
| Feature | Test File(s) | Status |
|---------|--------------|--------|
| Coop selection toggle | test_dashboard_page.py | ✅ |
| Manual refresh controls | test_dashboard_page.py | ✅ |
| System status (online/offline) | test_dashboard_page.py | ✅ |
| Temperature display | test_dashboard_page.py | ✅ |
| Humidity display | test_dashboard_page.py | ✅ |
| Door status | test_dashboard_page.py | ✅ |
| Check door button | test_dashboard_page.py | ✅ |
| Trend indicators | test_dashboard_page.py | ✅ |
| Threshold violation highlight | test_dashboard_page.py | ✅ |
| Live camera streaming | test_dashboard_page.py | ✅ |
| Sensor data charts | test_dashboard_page.py | ✅ |
| Time range selection (6h-30d) | test_dashboard_page.py | ✅ |
| Chart statistics (min/max/avg) | test_dashboard_page.py | ✅ |
| Video grid | test_dashboard_page.py | ✅ |
| Video filters (camera/date/sort) | test_dashboard_page.py | ✅ |
| Video pagination | test_dashboard_page.py | ✅ |
| Manual record button | test_dashboard_page.py | ✅ |
| Data export CSV | test_dashboard_page.py | ✅ |

### Chickens Page Features
| Feature | Test File(s) | Status |
|---------|--------------|--------|
| Chicken statistics cards | test_chicken_routes.py | ✅ |
| Chicken registry list | test_chicken_routes.py | ✅ |
| Add chicken form | test_chicken_routes.py | ✅ |
| Edit chicken modal | test_chicken_routes.py | ✅ |
| Deactivate chicken | test_chicken_routes.py | ✅ |
| Chicken card display | test_chicken_models.py | ✅ |

### Headcount Page Features
| Feature | Test File(s) | Status |
|---------|--------------|--------|
| Latest headcount display | test_headcount_routes.py | ✅ |
| Circular progress indicator | test_headcount_routes.py | ✅ |
| Confidence percentage | test_headcount_routes.py | ✅ |
| Detection method display | test_headcount_routes.py | ✅ |
| Headcount statistics | test_headcount_routes.py | ✅ |
| Success rate | test_headcount_routes.py | ✅ |
| Current streak | test_headcount_routes.py | ✅ |
| Historical log (30 records) | test_headcount_routes.py | ✅ |
| Headcount chart | test_headcount_routes.py | ✅ |
| Manual headcount trigger | test_headcount_routes.py | ✅ |

### Alerts Page Features
| Feature | Test File(s) | Status |
|---------|--------------|--------|
| Alert types overview | test_alert_routes.py | ✅ |
| Temperature low alerts | test_alert_routes.py | ✅ |
| Temperature high alerts | test_alert_routes.py | ✅ |
| System status alerts | test_alert_routes.py | ✅ |
| Motion detection alerts | test_alert_routes.py | ✅ |
| Email subscription form | test_alert_routes.py | ✅ |
| Subscription confirmation | test_alert_routes.py | ✅ |
| Current subscriptions display | test_alert_routes.py | ✅ |
| Check subscription status | test_alert_routes.py | ✅ |
| Edit subscription | test_alert_routes.py | ✅ |
| Unsubscribe | test_alert_routes.py | ✅ |
| Test alert buttons | test_alert_routes.py | ✅ |
| Alert history table | test_alert_routes.py | ✅ |
| History search/filter | test_alert_routes.py | ✅ |

### Settings Page Features
| Feature | Test File(s) | Status |
|---------|--------------|--------|
| Temperature unit preference | test_settings_routes.py | ✅ |
| Alert thresholds config | test_settings_routes.py | ✅ |
| Notification preferences | test_settings_routes.py | ✅ |
| Email notifications toggle | test_settings_routes.py | ✅ |
| Individual alert toggles | test_settings_routes.py | ✅ |
| Reset to defaults | test_settings_routes.py | ✅ |

### Admin Page Features
| Feature | Test File(s) | Status |
|---------|--------------|--------|
| Pi memory metrics | test_admin_routes.py | ✅ |
| Pi storage metrics | test_admin_routes.py | ✅ |
| S3 storage metrics | test_admin_routes.py | ✅ |
| AWS billing metrics | test_admin_routes.py | ✅ |
| Camera settings | test_admin_routes.py | ✅ |
| Motion recording toggle | test_admin_routes.py | ✅ |
| Nightly headcount settings | test_admin_routes.py | ✅ |
| Timezone selection | test_admin_routes.py | ✅ |
| Delete all videos | test_admin_routes.py | ✅ |
| Delete sensor data | test_admin_routes.py | ✅ |
| System restart script | test_admin_routes.py | ✅ |
| Health check script | test_admin_routes.py | ✅ |
| Performance monitor | test_admin_routes.py | ✅ |
| System update | test_admin_routes.py | ✅ |
| Service control (start/stop) | test_admin_routes.py | ✅ |
| Sensor diagnostics | test_admin_routes.py | ✅ |
| Climate control (fan) | test_admin_routes.py | ✅ |
| S3 scan/clean | test_admin_routes.py | ✅ |

### Diagnostics Page Features
| Feature | Test File(s) | Status |
|---------|--------------|--------|
| Run all diagnostics | test_diagnostics_routes.py | ✅ |
| Amplify config check | test_diagnostics_routes.py | ✅ |
| Auth session check | test_diagnostics_routes.py | ✅ |
| Cognito token check | test_diagnostics_routes.py | ✅ |
| Access token validity | test_diagnostics_routes.py | ✅ |
| AWS credentials check | test_diagnostics_routes.py | ✅ |
| Test API call | test_diagnostics_routes.py | ✅ |
| Force credential refresh | test_diagnostics_routes.py | ✅ |
| IAM policy status | test_diagnostics_routes.py | ✅ |
| Troubleshooting guides | test_diagnostics_routes.py | ✅ |

### Backend/Infrastructure Coverage
| Functionality | Phase | Test File(s) | Status |
|--------------|-------|--------------|--------|
| **Configuration** ||||
| Load JSON config | 1 | test_config_loader.py | ✅ |
| Validate config schema | 1 | test_config_validation.py | ✅ |
| Environment variables | 1 | test_environment.py | ✅ |
| Multi-coop config | 1 | test_config_loader.py | ✅ |
| **Logging** ||||
| Logger creation | 1 | test_logging_setup.py | ✅ |
| File rotation | 1 | test_logging_setup.py | ✅ |
| Coop ID in logs | 1 | test_logging_setup.py | ✅ |
| **Data Models** ||||
| Sensor readings | 1 | test_sensor_models.py | ✅ |
| Video metadata | 1 | test_video_models.py | ✅ |
| Chicken registry | 1 | test_chicken_models.py | ✅ |
| Headcount logs | 1 | test_chicken_models.py | ✅ |
| **Hardware** ||||
| Temperature sensor | 2 | test_sensor_interface.py | ✅ |
| Humidity sensor | 2 | test_sensor_interface.py | ✅ |
| Camera capture | 2 | test_camera_interface.py | ✅ |
| Video recording | 2 | test_camera_interface.py | ✅ |
| Motion detection | 2 | test_motion_detector.py | ✅ |
| **Persistence** ||||
| SQLite connection | 3 | test_database_connection.py | ✅ |
| User CRUD | 3 | test_database_connection.py | ✅ |
| CSV storage | 3 | test_csv_storage.py | ✅ |
| Daily file rotation | 3 | test_csv_storage.py | ✅ |
| CSV backup tracking | 3 | test_csv_storage.py | ✅ |
| **AWS Integration** ||||
| S3 upload/download | 4 | test_s3_client.py | ✅ |
| S3 presigned URLs | 4 | test_s3_client.py | ✅ |
| IoT Core publish | 4 | test_iot_client.py | ✅ |
| IoT topic management | 4 | test_iot_client.py | ✅ |
| SNS alerts | 4 | test_sns_client.py | ✅ |
| SNS subscriptions | 4 | test_sns_client.py | ✅ |
| **API Layer** ||||
| Password hashing | 5 | test_authentication.py | ✅ |
| Session management | 5 | test_authentication.py | ✅ |
| CSRF protection | 5 | test_authentication.py | ✅ |
| Sensor routes | 5 | test_sensor_routes.py | ✅ |
| Video routes | 5 | test_video_routes.py | ✅ |
| Video retention | 5 | test_video_routes.py | ✅ |
| Chicken routes | 5 | test_chicken_routes.py | ✅ |
| Headcount routes | 5 | test_headcount_routes.py | ✅ |
| Settings routes | 5 | test_settings_routes.py | ✅ |
| Admin routes | 5 | test_admin_routes.py | ✅ |
| Alert routes | 5 | test_alert_routes.py | ✅ |
| Diagnostics routes | 5 | test_diagnostics_routes.py | ✅ |
| **Frontend Services** ||||
| API client | 6 | test_api_service.py | ✅ |
| IoT WebSocket | 6 | test_iot_websocket.py | ✅ |
| Dashboard page | 6 | test_dashboard_page.py | ✅ |
| **Integration** ||||
| Sensor pipeline | 7 | test_sensor_to_cloud.py | ✅ |
| User authentication | 7 | test_user_flows.py | ✅ |
| Video management | 7 | test_user_flows.py | ✅ |
| Headcount | 7 | test_user_flows.py | ✅ |
| **DevOps/CI-CD** ||||
| GitHub Actions workflow | 8 | test_github_actions.py | ✅ |
| Change detection | 8 | test_github_actions.py | ✅ |
| Deployment scripts | 8 | test_deploy_script.py | ✅ |
| Health checks | 8 | test_health_check.py | ✅ |
| Systemd services | 8 | test_systemd_services.py | ✅ |
| Service management | 8 | test_systemd_services.py | ✅ |
| Auto-updates | 8 | test_auto_update.py | ✅ |
| Pi device updates | 8 | test_deploy_script.py | ✅ |
| **Edge Resilience** ||||
| Power recovery | 9 | test_power_recovery.py | ✅ |
| Offline operation | 9 | test_offline_operation.py | ✅ |
| Local data buffering | 9 | test_offline_operation.py | ✅ |
| Data synchronization | 9 | test_data_sync.py | ✅ |
| Local storage management | 9 | test_local_storage.py | ✅ |
| Connection retry | 9 | test_connection_retry.py | ✅ |
| Circuit breaker pattern | 9 | test_connection_retry.py | ✅ |

| **Security Hardening** ||||
| Input validation | 10 | test_input_validation.py | ✅ |
| SQL injection prevention | 10 | test_input_validation.py | ✅ |
| Command injection prevention | 10 | test_input_validation.py | ✅ |
| Secret management | 10 | test_secret_management.py | ✅ |
| API rate limiting | 10 | test_api_security.py | ✅ |
| CORS/CSRF protection | 10 | test_api_security.py | ✅ |
| Audit logging | 10 | test_audit_logging.py | ✅ |
| **Code Quality** ||||
| Module structure | 11 | test_module_structure.py | ✅ |
| Design patterns | 11 | test_design_patterns.py | ✅ |
| Interface contracts | 11 | test_interface_contracts.py | ✅ |
| **Advanced Alerting** ||||
| Webhook notifications | 12 | test_webhook_notifications.py | ✅ |
| Alert routing | 12 | test_alert_routing.py | ✅ |
| Alert aggregation | 12 | test_alert_aggregation.py | ✅ |
| **Command Queue** ||||
| DynamoDB command queue | 13 | test_command_queue.py | ✅ |
| Job management | 13 | test_job_management.py | ✅ |
| **RBAC** ||||
| User roles | 14 | test_user_roles.py | ✅ |
| Permissions | 14 | test_permissions.py | ✅ |
| **Real-Time Streaming** ||||
| Live streaming | 15 | test_live_streaming.py | ✅ |
| Stream protocols | 15 | test_stream_protocols.py | ✅ |
| **Multi-Camera Intelligence** ||||
| Detection zones | 16 | test_detection_zones.py | ✅ |
| Chicken counting | 16 | test_chicken_counting.py | ✅ |
| **Backup & DR** ||||
| Data backup | 17 | test_data_backup.py | ✅ |
| Disaster recovery | 17 | test_disaster_recovery.py | ✅ |
| Failover | 17 | test_failover.py | ✅ |
| **Observability** ||||
| Metrics collection | 18 | test_metrics_collection.py | ✅ |
| Distributed tracing | 18 | test_distributed_tracing.py | ✅ |
| Performance monitoring | 18 | test_performance_monitoring.py | ✅ |

**Legend:**
- ✅ = Test exists and covers functionality
- All 18 phases now covered: Foundation through Observability!

---

## Phase 8: DevOps & CI/CD

Phase 8 tests the deployment pipeline and device update mechanisms.

### 8.1 GitHub Actions Workflow (`test_github_actions.py`)

**Functionality Being Tested:**
- Workflow trigger conditions (push to main, PRs, manual dispatch)
- Change detection for conditional deployments
- CI job configuration and dependencies
- Deployment job prerequisites
- Concurrency control and secret handling

**Why This Matters:**
The CI/CD pipeline ensures code quality and automates deployments. Broken
pipeline configuration can prevent deployments or allow untested code to
reach production.

**How Tests Are Executed:**

```bash
pytest tdd/phase8_devops/cicd/test_github_actions.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_workflow_triggers_on_push_to_main` | Verify automatic triggers |
| `test_python_file_patterns` | Pi updates on hardware changes |
| `test_deploy_backend_requires_ci` | Ensure CI passes before deploy |
| `test_no_hardcoded_secrets` | Security validation |

---

### 8.2 Deployment Scripts (`test_deploy_script.py`)

**Functionality Being Tested:**
- deploy.sh multi-coop deployment
- Git operations (stage, commit, push)
- SSH connectivity to Raspberry Pis
- Service restart on each Pi
- Stash handling for local changes

**Why This Matters:**
The deploy.sh script is the primary mechanism for pushing updates to
Raspberry Pi devices. It must reliably commit changes, push to GitHub,
SSH to each Pi, pull updates, and restart services.

**How Tests Are Executed:**

```bash
pytest tdd/phase8_devops/deployment/test_deploy_script.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_deploys_to_coop1` | Deploy to first Pi |
| `test_deploys_to_coop2` | Deploy to second Pi |
| `test_restarts_chickencoop_service` | Service restart |
| `test_verifies_service_running` | Deployment verification |

---

### 8.3 Health Check Scripts (`test_health_check.py`)

**Functionality Being Tested:**
- Lambda endpoint validation
- HTTP status code verification
- CORS header checking
- Retry logic for transient failures
- Lambda URL fetching from CloudFormation

**Why This Matters:**
Health checks run after deployments to verify the system is working.
They catch deployment issues before users encounter them.

**How Tests Are Executed:**

```bash
pytest tdd/phase8_devops/deployment/test_health_check.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_checks_status_endpoint` | Verify status API |
| `test_has_retry_mechanism` | Handle transient failures |
| `test_exits_nonzero_on_failure` | Block failed deployments |
| `test_updates_amplify_outputs` | Configure Lambda URLs |

---

### 8.4 Systemd Services (`test_systemd_services.py`)

**Functionality Being Tested:**
- Service file structure and syntax
- Service dependencies (After, Wants)
- Restart behavior and recovery
- Environment variable configuration (COOP_ID)
- Log output configuration
- Service installation and management scripts

**Why This Matters:**
Systemd services ensure the monitoring daemon runs continuously on each Pi.
Proper configuration ensures the service starts on boot, restarts after
failures, and logs appropriately.

**How Tests Are Executed:**

```bash
pytest tdd/phase8_devops/services/test_systemd_services.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_restart_always` | Auto-restart on failure |
| `test_sets_coop_id` | Multi-coop environment |
| `test_runs_as_pi_user` | Security (non-root) |
| `test_enables_service` | Auto-start on boot |

---

### 8.5 Auto-Update Scripts (`test_auto_update.py`)

**Functionality Being Tested:**
- System package updates (apt update/upgrade)
- Python dependency updates (pip)
- Kernel update detection and reboot scheduling
- Hostname-based device detection

**Why This Matters:**
Auto-updates keep Raspberry Pi systems secure with latest patches.
The script handles updates gracefully and schedules reboots for
off-hours to minimize disruption.

**How Tests Are Executed:**

```bash
pytest tdd/phase8_devops/deployment/test_auto_update.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_runs_apt_upgrade` | System updates |
| `test_updates_pip_packages` | Python dependencies |
| `test_schedules_reboot_for_offhours` | Minimal disruption |
| `test_uses_hostname_detection` | Multi-device support |

---

### CI/CD Pipeline Coverage

| Feature | Test File(s) | Status |
|---------|--------------|--------|
| Push to main triggers workflow | test_github_actions.py | ✅ |
| PR triggers CI only | test_github_actions.py | ✅ |
| Manual dispatch support | test_github_actions.py | ✅ |
| Python file changes → Pi update | test_github_actions.py | ✅ |
| Backend changes → Lambda deploy | test_github_actions.py | ✅ |
| WebApp changes → React deploy | test_github_actions.py | ✅ |
| Config changes → Pi update | test_github_actions.py | ✅ |
| CI must pass before deploy | test_github_actions.py | ✅ |
| Multi-coop deployment | test_deploy_script.py | ✅ |
| SSH to Raspberry Pis | test_deploy_script.py | ✅ |
| Git pull on each Pi | test_deploy_script.py | ✅ |
| Service restart verification | test_deploy_script.py | ✅ |
| Lambda health checks | test_health_check.py | ✅ |
| Health check retry logic | test_health_check.py | ✅ |
| Lambda URL fetching | test_health_check.py | ✅ |
| Systemd service config | test_systemd_services.py | ✅ |
| Service auto-restart | test_systemd_services.py | ✅ |
| Service installation | test_systemd_services.py | ✅ |
| System package updates | test_auto_update.py | ✅ |
| Python dependency updates | test_auto_update.py | ✅ |
| Kernel update handling | test_auto_update.py | ✅ |

---

## Phase 9: Edge Resilience & Offline Operation

Phase 9 ensures reliable operation in austere environments with unreliable power and WiFi connectivity. The Raspberry Pi devices must continue monitoring even when disconnected and recover gracefully after disruptions.

### 9.1 Power Recovery (`test_power_recovery.py`)

**Functionality Being Tested:**
- Graceful startup after unexpected shutdown
- State restoration from persistent storage
- Incomplete operation cleanup (partial videos, temp files)
- Service auto-start on boot
- Hardware re-initialization sequence
- Filesystem integrity checks

**Why This Matters:**
Raspberry Pis in chicken coops may experience frequent power outages. The system must start reliably when power returns, resume monitoring without manual intervention, and clean up any corrupted state from the interruption.

**How Tests Are Executed:**

```bash
pytest tdd/phase9_resilience/power/test_power_recovery.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_service_starts_on_boot` | Auto-start after power restore |
| `test_startup_waits_for_network` | Don't start before network ready |
| `test_partial_video_cleanup` | Clean corrupted recordings |
| `test_database_integrity_check` | Verify SQLite not corrupted |
| `test_camera_reconnect_on_startup` | Re-initialize camera hardware |

---

### 9.2 Offline Operation (`test_offline_operation.py`)

**Functionality Being Tested:**
- Continued sensor monitoring without connectivity
- Local data buffering during WiFi outages
- Video storage on local SD card
- Graceful degradation of cloud-dependent features
- Network status detection and reporting

**Why This Matters:**
WiFi in rural/austere environments is unreliable. The monitoring system must continue its primary function even when disconnected. All data must be preserved locally and synchronized when connectivity returns.

**How Tests Are Executed:**

```bash
pytest tdd/phase9_resilience/connectivity/test_offline_operation.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_sensor_readings_continue_offline` | Core monitoring works offline |
| `test_motion_detection_continues_offline` | Recording triggers work offline |
| `test_sensor_data_buffered_locally` | Data saved to local storage |
| `test_videos_stored_locally` | Videos saved when S3 unavailable |
| `test_no_crash_on_network_error` | Network errors handled gracefully |

---

### 9.3 Data Synchronization (`test_data_sync.py`)

**Functionality Being Tested:**
- Buffered sensor data upload to S3/IoT when online
- Pending video upload queue processing
- Alert delivery for buffered alerts
- Sync prioritization and ordering
- Bandwidth-aware upload throttling
- Conflict resolution for settings

**Why This Matters:**
After a network outage (minutes, hours, or days), all buffered data must be synchronized to the cloud reliably. The sync must be complete (no data lost), ordered (chronological), efficient (don't overwhelm connection), and resumable.

**How Tests Are Executed:**

```bash
pytest tdd/phase9_resilience/connectivity/test_data_sync.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_sync_starts_on_reconnection` | Auto-sync when online |
| `test_all_buffered_readings_uploaded` | No data loss |
| `test_readings_uploaded_in_chronological_order` | Maintain order |
| `test_critical_data_synced_first` | Alerts before routine data |
| `test_partial_upload_resumable` | Handle interruptions |

---

### 9.4 Local Storage Management (`test_local_storage.py`)

**Functionality Being Tested:**
- SD card space monitoring and management
- Data retention policies during extended outages
- Priority-based storage allocation
- Automatic cleanup when storage is low
- Protection of data pending sync

**Why This Matters:**
During extended network outages, the Raspberry Pi must manage limited SD card storage wisely. Without proper management, the disk could fill up and cause the system to fail.

**How Tests Are Executed:**

```bash
pytest tdd/phase9_resilience/storage/test_local_storage.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_storage_threshold_warning` | Alert when disk filling |
| `test_oldest_videos_deleted_first` | FIFO cleanup |
| `test_pending_data_not_deleted` | Protect unsynced data |
| `test_reserved_space_for_system` | Don't fill disk 100% |
| `test_motion_frames_in_tmpfs` | Reduce SD card wear |

---

### 9.5 Connection Retry (`test_connection_retry.py`)

**Functionality Being Tested:**
- WiFi reconnection with exponential backoff
- AWS service reconnection (S3, IoT, SNS)
- Circuit breaker pattern for failing services
- Connection pooling and reuse
- Timeout handling

**Why This Matters:**
Connections are unreliable in austere environments. The system needs intelligent retry logic that recovers quickly from brief outages, doesn't waste resources on hopeless retries, and resumes normal operation when service returns.

**How Tests Are Executed:**

```bash
pytest tdd/phase9_resilience/connectivity/test_connection_retry.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_auto_reconnect_on_disconnect` | Auto WiFi reconnect |
| `test_reconnect_uses_backoff` | Exponential backoff |
| `test_circuit_opens_on_failures` | Stop hopeless retries |
| `test_s3_failure_continues_local` | Graceful degradation |
| `test_partial_upload_resumable` | Resume interrupted uploads |

---

### Edge Resilience Coverage

| Feature | Test File(s) | Status |
|---------|--------------|--------|
| **Power Recovery** |||
| Auto-start on boot | test_power_recovery.py | ✅ |
| Wait for network before start | test_power_recovery.py | ✅ |
| State restoration | test_power_recovery.py | ✅ |
| Partial video cleanup | test_power_recovery.py | ✅ |
| Hardware re-initialization | test_power_recovery.py | ✅ |
| Filesystem integrity check | test_power_recovery.py | ✅ |
| **Offline Operation** |||
| Continue monitoring offline | test_offline_operation.py | ✅ |
| Local sensor data buffering | test_offline_operation.py | ✅ |
| Local video storage | test_offline_operation.py | ✅ |
| Network status detection | test_offline_operation.py | ✅ |
| Graceful degradation | test_offline_operation.py | ✅ |
| **Data Synchronization** |||
| Auto-sync on reconnection | test_data_sync.py | ✅ |
| Chronological upload order | test_data_sync.py | ✅ |
| Priority-based sync | test_data_sync.py | ✅ |
| Bandwidth throttling | test_data_sync.py | ✅ |
| Resumable uploads | test_data_sync.py | ✅ |
| **Storage Management** |||
| Disk space monitoring | test_local_storage.py | ✅ |
| Automatic cleanup | test_local_storage.py | ✅ |
| Pending data protection | test_local_storage.py | ✅ |
| Tmpfs for temp data | test_local_storage.py | ✅ |
| **Connection Retry** |||
| WiFi auto-reconnect | test_connection_retry.py | ✅ |
| Exponential backoff | test_connection_retry.py | ✅ |
| Circuit breaker pattern | test_connection_retry.py | ✅ |
| Service-level degradation | test_connection_retry.py | ✅ |

---

## Phase 10: Security Hardening

Phase 10 implements security best practices to protect against common attack vectors and ensure data integrity.

### 10.1 Input Validation (`test_input_validation.py`)

**Functionality Being Tested:**
- JSON schema validation for all API inputs
- COOP_ID allowlist enforcement
- SQL injection prevention
- Command injection prevention
- Path traversal prevention
- XSS input sanitization

**Why This Matters:**
User input is the primary attack vector for web applications. Proper validation prevents injection attacks that could compromise data, execute malicious code, or access unauthorized resources.

**How Tests Are Executed:**

```bash
pytest tdd/phase10_security/validation/test_input_validation.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_json_schema_validates` | Enforce input structure |
| `test_coop_id_must_be_in_allowlist` | Prevent arbitrary coop access |
| `test_sql_injection_prevented` | Block SQL attacks |
| `test_command_injection_prevented` | Block shell attacks |
| `test_path_traversal_blocked` | Prevent file access attacks |

---

### 10.2 Secret Management (`test_secret_management.py`)

**Functionality Being Tested:**
- No hardcoded credentials in codebase
- Environment variable usage for secrets
- AWS Secrets Manager integration
- Secret rotation support
- Secure secret logging (no plaintext)

**Why This Matters:**
Exposed secrets are the #1 cause of cloud security breaches. Proper secret management ensures credentials are never committed to code, logged in plaintext, or accessible to unauthorized parties.

**How Tests Are Executed:**

```bash
pytest tdd/phase10_security/secrets/test_secret_management.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_no_hardcoded_aws_credentials` | Scan code for secrets |
| `test_secrets_loaded_from_environment` | Verify env var usage |
| `test_secrets_manager_integration` | AWS secrets retrieval |
| `test_secrets_not_logged` | Prevent secret leakage |

---

### 10.3 API Security (`test_api_security.py`)

**Functionality Being Tested:**
- Rate limiting per endpoint
- CORS policy enforcement
- CSRF protection for state-changing requests
- Authentication header validation
- Content-Type enforcement
- Security headers (X-Frame-Options, etc.)

**Why This Matters:**
API security prevents abuse, protects against cross-origin attacks, and ensures only authorized clients can access resources.

**How Tests Are Executed:**

```bash
pytest tdd/phase10_security/api/test_api_security.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_rate_limit_enforced` | Prevent abuse/DoS |
| `test_cors_rejects_unknown_origins` | Block cross-origin attacks |
| `test_csrf_token_required` | Prevent CSRF attacks |
| `test_auth_header_required` | Enforce authentication |

---

### 10.4 Audit Logging (`test_audit_logging.py`)

**Functionality Being Tested:**
- Security event logging (login attempts, permission denials)
- Audit trail completeness
- Log integrity protection
- Log retention compliance
- Sensitive data redaction in logs

**Why This Matters:**
Audit logs are essential for security incident investigation, compliance requirements, and detecting unauthorized access patterns.

**How Tests Are Executed:**

```bash
pytest tdd/phase10_security/audit/test_audit_logging.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_login_attempts_logged` | Track authentication |
| `test_permission_denials_logged` | Track access attempts |
| `test_log_integrity_verified` | Detect tampering |
| `test_sensitive_data_redacted` | Protect PII in logs |

---

## Phase 11: Code Quality & Modularity

Phase 11 ensures the codebase follows best practices for maintainability, readability, and extensibility.

### 11.1 Module Structure (`test_module_structure.py`)

**Functionality Being Tested:**
- File size limits (max 500 lines)
- Single responsibility per module
- Proper module documentation
- Circular dependency prevention
- Import organization

**Why This Matters:**
Well-structured code is easier to understand, test, and maintain. Large files and circular dependencies make refactoring difficult and increase bug likelihood.

**How Tests Are Executed:**

```bash
pytest tdd/phase11_code_quality/structure/test_module_structure.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_file_size_under_limit` | Prevent monolithic files |
| `test_single_responsibility` | Focused modules |
| `test_no_circular_dependencies` | Clean architecture |
| `test_module_has_docstring` | Documentation |

---

### 11.2 Design Patterns (`test_design_patterns.py`)

**Functionality Being Tested:**
- Singleton pattern for shared resources
- Factory pattern for object creation
- Repository pattern for data access
- Service layer separation
- Dependency injection support

**Why This Matters:**
Consistent design patterns make the codebase predictable and easier for new developers to understand. They also enable better testing through dependency injection.

**How Tests Are Executed:**

```bash
pytest tdd/phase11_code_quality/patterns/test_design_patterns.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_singleton_same_instance` | Shared resources |
| `test_factory_creates_instances` | Object creation |
| `test_repository_abstracts_storage` | Data access |
| `test_dependencies_injectable` | Testability |

---

### 11.3 Interface Contracts (`test_interface_contracts.py`)

**Functionality Being Tested:**
- Abstract base classes for interfaces
- Type hints on public methods
- Return type consistency
- Interface documentation
- Contract enforcement

**Why This Matters:**
Clear interfaces define how components interact. Type hints catch errors at development time and enable IDE assistance. Consistent contracts make the system predictable.

**How Tests Are Executed:**

```bash
pytest tdd/phase11_code_quality/interfaces/test_interface_contracts.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_interface_has_abstract_methods` | Enforce contracts |
| `test_public_methods_have_type_hints` | Type safety |
| `test_interface_documented` | Clear expectations |
| `test_implementations_match_interface` | Contract compliance |

---

## Phase 12: Advanced Alerting

Phase 12 extends the alerting system with multiple channels, smart routing, and aggregation.

### 12.1 Webhook Notifications (`test_webhook_notifications.py`)

**Functionality Being Tested:**
- Slack webhook integration
- Discord webhook integration
- Custom webhook endpoints
- Webhook retry logic
- Webhook authentication

**Why This Matters:**
Different users prefer different notification channels. Webhook support enables integration with team collaboration tools and custom notification systems.

**How Tests Are Executed:**

```bash
pytest tdd/phase12_alerting/webhooks/test_webhook_notifications.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_slack_webhook_sends` | Slack integration |
| `test_discord_webhook_sends` | Discord integration |
| `test_custom_webhook_authentication` | Secure webhooks |
| `test_webhook_retry_on_failure` | Reliability |

---

### 12.2 Alert Routing (`test_alert_routing.py`)

**Functionality Being Tested:**
- Route alerts by type (temperature, motion, headcount)
- Route alerts by severity
- Time-based routing (quiet hours)
- Escalation paths
- Routing rule configuration

**Why This Matters:**
Not all alerts are equally urgent. Temperature alerts need immediate attention; motion alerts may be routine. Routing ensures the right people get notified at the right time.

**How Tests Are Executed:**

```bash
pytest tdd/phase12_alerting/routing/test_alert_routing.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_route_by_alert_type` | Type-based routing |
| `test_route_by_severity` | Priority routing |
| `test_quiet_hours_respected` | Time-based routing |
| `test_escalation_after_timeout` | Escalation |

---

### 12.3 Alert Aggregation (`test_alert_aggregation.py`)

**Functionality Being Tested:**
- Alert debouncing (prevent rapid repeat alerts)
- Alert digests (daily summary)
- Alert correlation (related alerts grouped)
- Alert trend detection

**Why This Matters:**
Alert fatigue causes important alerts to be ignored. Aggregation reduces noise while ensuring critical alerts aren't lost in a flood of notifications.

**How Tests Are Executed:**

```bash
pytest tdd/phase12_alerting/aggregation/test_alert_aggregation.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_debounce_rapid_alerts` | Reduce noise |
| `test_daily_digest_generated` | Summary alerts |
| `test_related_alerts_grouped` | Correlation |
| `test_trend_detected` | Pattern recognition |

---

## Phase 13: Command Queue

Phase 13 implements a reliable command queue for remote Pi control operations.

### 13.1 Command Queue (`test_command_queue.py`)

**Functionality Being Tested:**
- DynamoDB-backed command queue
- FIFO command ordering
- Command deduplication
- Dead letter queue for failed commands
- Command TTL (expiration)

**Why This Matters:**
Remote commands (restart, record video, check door) must be reliably delivered even if the Pi is temporarily offline. A persistent queue ensures commands are eventually executed.

**How Tests Are Executed:**

```bash
pytest tdd/phase13_command_queue/queue/test_command_queue.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_command_enqueued` | Queue insertion |
| `test_fifo_ordering` | Order preservation |
| `test_duplicate_commands_rejected` | Deduplication |
| `test_expired_commands_discarded` | TTL handling |

---

### 13.2 Job Management (`test_job_management.py`)

**Functionality Being Tested:**
- Job status tracking (pending, running, completed, failed)
- Job progress reporting
- Job cancellation
- Job retry with backoff
- Job history retention

**Why This Matters:**
Long-running commands (video upload, firmware update) need status tracking. Users should see progress and be able to cancel operations if needed.

**How Tests Are Executed:**

```bash
pytest tdd/phase13_command_queue/jobs/test_job_management.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_job_status_tracked` | Status visibility |
| `test_job_progress_reported` | Progress updates |
| `test_job_cancellable` | User control |
| `test_failed_job_retried` | Reliability |

---

## Phase 14: Role-Based Access Control

Phase 14 implements fine-grained access control for multi-user environments.

### 14.1 User Roles (`test_user_roles.py`)

**Functionality Being Tested:**
- Owner role (full access to all coops)
- Admin role (manage users, settings)
- Viewer role (read-only access)
- Role assignment and modification
- Role hierarchy

**Why This Matters:**
Multi-user farms need different access levels. Owners manage everything; admins help with configuration; viewers just monitor. RBAC prevents unauthorized changes.

**How Tests Are Executed:**

```bash
pytest tdd/phase14_rbac/roles/test_user_roles.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_owner_has_full_access` | Owner privileges |
| `test_admin_can_manage_users` | Admin scope |
| `test_viewer_cannot_modify` | Read-only access |
| `test_role_hierarchy_enforced` | Inheritance |

---

### 14.2 Permissions (`test_permissions.py`)

**Functionality Being Tested:**
- Per-coop permission grants
- Permission checking decorator
- Explicit deny rules
- Permission caching
- Permission audit trail

**Why This Matters:**
Fine-grained permissions allow sharing access to specific coops without granting full account access. This enables scenarios like letting neighbors monitor their coop.

**How Tests Are Executed:**

```bash
pytest tdd/phase14_rbac/permissions/test_permissions.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_permission_granted_for_coop` | Coop-level access |
| `test_permission_decorator_blocks` | Enforcement |
| `test_explicit_deny_overrides` | Deny rules |
| `test_permission_changes_logged` | Audit trail |

---

## Phase 15: Real-Time Streaming

Phase 15 enables live video streaming from coop cameras.

### 15.1 Live Streaming (`test_live_streaming.py`)

**Functionality Being Tested:**
- Stream session initiation
- Stream URL generation
- Session timeout handling
- Concurrent viewer limits
- Stream quality adaptation

**Why This Matters:**
Live streaming lets users check on their chickens in real-time without waiting for recorded video. It's essential for monitoring during critical situations.

**How Tests Are Executed:**

```bash
pytest tdd/phase15_streaming/live/test_live_streaming.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_stream_session_created` | Session management |
| `test_stream_url_generated` | URL generation |
| `test_session_expires` | Resource cleanup |
| `test_quality_adapts_to_bandwidth` | Adaptive bitrate |

---

### 15.2 Stream Protocols (`test_stream_protocols.py`)

**Functionality Being Tested:**
- HLS (HTTP Live Streaming) support
- WebRTC support for low-latency
- Protocol negotiation
- Fallback handling

**Why This Matters:**
Different devices and network conditions require different streaming protocols. HLS works everywhere but has latency; WebRTC is low-latency but needs modern browsers.

**How Tests Are Executed:**

```bash
pytest tdd/phase15_streaming/protocols/test_stream_protocols.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_hls_segments_generated` | HLS support |
| `test_webrtc_connection` | WebRTC support |
| `test_protocol_negotiation` | Client compatibility |
| `test_fallback_to_hls` | Graceful degradation |

---

## Phase 16: Multi-Camera Intelligence

Phase 16 adds advanced computer vision features for multi-camera setups.

### 16.1 Detection Zones (`test_detection_zones.py`)

**Functionality Being Tested:**
- Configurable detection zones per camera
- Zone exclusion (ignore areas)
- Zone-specific sensitivity
- Zone overlap handling
- Zone visualization

**Why This Matters:**
Not all areas of the camera view are equally important. Detection zones let users focus motion detection on specific areas (door, roosting bars) and ignore others (trees outside).

**How Tests Are Executed:**

```bash
pytest tdd/phase16_camera_intelligence/zones/test_detection_zones.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_detection_only_in_zone` | Zone focus |
| `test_exclude_zone_ignored` | Exclusion zones |
| `test_zone_sensitivity` | Per-zone tuning |
| `test_zones_visualized` | UI overlay |

---

### 16.2 Chicken Counting (`test_chicken_counting.py`)

**Functionality Being Tested:**
- Multi-frame chicken tracking
- Occlusion handling
- Cross-camera correlation
- Count confidence scoring
- Movement pattern analysis

**Why This Matters:**
Automated headcount is a core safety feature. Multi-frame tracking improves accuracy over single-frame detection by tracking individuals through occlusion and movement.

**How Tests Are Executed:**

```bash
pytest tdd/phase16_camera_intelligence/counting/test_chicken_counting.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_track_across_frames` | Multi-frame tracking |
| `test_handle_occlusion` | Occlusion handling |
| `test_cross_camera_correlation` | Camera correlation |
| `test_count_confidence` | Accuracy scoring |

---

## Phase 17: Backup & Disaster Recovery

Phase 17 ensures data protection and system recoverability.

### 17.1 Data Backup (`test_data_backup.py`)

**Functionality Being Tested:**
- Video backup to secondary storage
- Configuration backup
- Database backup
- Backup verification
- Backup scheduling

**Why This Matters:**
Hardware failures, SD card corruption, and accidental deletion can cause data loss. Regular backups to secondary storage ensure data can be recovered.

**How Tests Are Executed:**

```bash
pytest tdd/phase17_backup_dr/backup/test_data_backup.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_videos_backed_up` | Video protection |
| `test_config_backed_up` | Settings protection |
| `test_backup_verified` | Integrity check |
| `test_backup_scheduled` | Automation |

---

### 17.2 Disaster Recovery (`test_disaster_recovery.py`)

**Functionality Being Tested:**
- Restore videos from backup
- Restore configuration from backup
- Database restoration
- Configuration rollback
- Recovery Time Objective (RTO) testing

**Why This Matters:**
Backups are useless if they can't be restored. DR testing verifies the complete recovery process works and meets time objectives.

**How Tests Are Executed:**

```bash
pytest tdd/phase17_backup_dr/recovery/test_disaster_recovery.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_restore_videos` | Video recovery |
| `test_restore_config` | Settings recovery |
| `test_rollback_to_previous` | Config rollback |
| `test_rto_achievable` | Recovery time |

---

### 17.3 Failover (`test_failover.py`)

**Functionality Being Tested:**
- Cross-coop failover detection
- Automatic failover triggering
- Failover notification
- Failback procedures

**Why This Matters:**
If one coop's Pi fails, another may be able to provide limited monitoring. Automatic failover detection and notification helps maintain visibility into chicken welfare.

**How Tests Are Executed:**

```bash
pytest tdd/phase17_backup_dr/failover/test_failover.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_detect_pi_offline` | Failure detection |
| `test_failover_triggered` | Auto failover |
| `test_failover_notification` | Alert on failover |
| `test_automatic_failback` | Resume normal |

---

## Phase 18: Performance & Observability

Phase 18 implements comprehensive monitoring, tracing, and performance management.

### 18.1 Metrics Collection (`test_metrics_collection.py`)

**Functionality Being Tested:**
- System metrics (CPU, memory, disk, temperature)
- Application metrics (processing time, queue depth)
- Business metrics (videos recorded, alerts sent)
- Metric aggregation and storage
- CloudWatch integration

**Why This Matters:**
Metrics provide visibility into system health and performance. They enable proactive issue detection, capacity planning, and performance optimization.

**How Tests Are Executed:**

```bash
pytest tdd/phase18_observability/metrics/test_metrics_collection.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_cpu_usage_collected` | System metrics |
| `test_motion_detection_time` | App metrics |
| `test_videos_recorded_count` | Business metrics |
| `test_metrics_sent_to_cloudwatch` | CloudWatch |

---

### 18.2 Distributed Tracing (`test_distributed_tracing.py`)

**Functionality Being Tested:**
- Request correlation IDs
- End-to-end trace collection
- Trace visualization
- AWS X-Ray integration
- Slow span identification

**Why This Matters:**
Distributed tracing helps identify where time is spent in complex operations. It's essential for debugging performance issues that span multiple services (Pi → Lambda → S3).

**How Tests Are Executed:**

```bash
pytest tdd/phase18_observability/tracing/test_distributed_tracing.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_correlation_id_generated` | Request tracking |
| `test_trace_spans_created` | Span collection |
| `test_traces_sent_to_xray` | X-Ray integration |
| `test_identify_slow_spans` | Bottleneck detection |

---

### 18.3 Performance Monitoring (`test_performance_monitoring.py`)

**Functionality Being Tested:**
- Performance baseline establishment
- Anomaly detection
- Automated optimization suggestions
- Capacity planning data

**Why This Matters:**
Continuous performance monitoring catches degradation before users notice. Baselines and anomaly detection enable proactive fixes. Capacity planning prevents running out of resources.

**How Tests Are Executed:**

```bash
pytest tdd/phase18_observability/performance/test_performance_monitoring.py -v
```

**Key Test Cases:**
| Test | Purpose |
|------|---------|
| `test_baseline_calculated` | Establish baseline |
| `test_slow_operation_detected` | Anomaly detection |
| `test_suggestion_for_slow_upload` | Optimization |
| `test_storage_projection` | Capacity planning |

---

## Running the Complete Test Suite

```bash
# Run all phases in order
pytest tdd/ -v --tb=short

# Run with coverage report
pytest tdd/ -v --cov=src --cov-report=html --cov-report=term-missing

# Run specific phase
pytest tdd/phase1_foundation/ -v

# Run specific test file
pytest tdd/phase1_foundation/config/test_config_loader.py -v

# Run specific test
pytest tdd/phase1_foundation/config/test_config_loader.py::TestConfigLoader::test_load_config_returns_dict -v

# Run tests matching a pattern
pytest tdd/ -v -k "temperature"

# Run with verbose failure output
pytest tdd/ -v --tb=long

# Run and stop on first failure
pytest tdd/ -v -x
```
