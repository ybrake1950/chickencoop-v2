#!/bin/bash
#
# Health Check Script for Chicken Coop Lambda Endpoints
# Validates deployment by checking API endpoints are responsive
#

set -e

# Configuration
MAX_RETRIES=3
RETRY_DELAY=5
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
AMPLIFY_OUTPUTS="$PROJECT_ROOT/webapp/amplify_outputs.json"

# Log an informational message.
# Arguments:
#   $1 - Message to log
log_info() {
    echo "[INFO] $1"
}

# Log an error message.
# Arguments:
#   $1 - Error message to log
log_error() {
    echo "[ERROR] $1"
}

# Retrieve a Lambda API URL from amplify_outputs.json.
# Arguments:
#   $1 - Endpoint name (e.g., "status", "sensorData", "videos")
# Returns:
#   The URL string if found, empty string otherwise
get_api_url() {
    local endpoint_name=$1
    if [ -f "$AMPLIFY_OUTPUTS" ]; then
        jq -r ".custom.${endpoint_name}Url // empty" "$AMPLIFY_OUTPUTS"
    fi
}

# Check a single API endpoint with retry logic.
# Attempts up to MAX_RETRIES times with RETRY_DELAY seconds between attempts.
# Arguments:
#   $1 - Endpoint name for logging
#   $2 - URL to check
# Returns:
#   0 if endpoint responds with HTTP 200 or 204, 1 otherwise
check_endpoint() {
    local name=$1
    local url=$2
    local attempt=1

    if [ -z "$url" ]; then
        log_info "No URL configured for $name endpoint"
        return 0
    fi

    log_info "Checking $name endpoint: $url"

    while [ $attempt -le $MAX_RETRIES ]; do
        log_info "Attempt $attempt of $MAX_RETRIES for $name"

        # Use curl to check endpoint
        http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 30 "$url" 2>/dev/null || echo "000")

        # Check for successful HTTP status codes (200 or 204)
        if [ "$http_code" = "200" ] || [ "$http_code" = "204" ]; then
            log_info "$name endpoint returned HTTP $http_code - OK"
            return 0
        fi

        log_info "$name endpoint returned HTTP $http_code on attempt $attempt"

        if [ $attempt -lt $MAX_RETRIES ]; then
            sleep $RETRY_DELAY
        fi

        attempt=$((attempt + 1))
    done

    log_error "Health check failed for $name endpoint after $MAX_RETRIES attempts"
    log_error "Check CloudWatch logs for Lambda errors"
    log_error "Review CloudFormation stack events for deployment issues"
    return 1
}

# Main entry point for health check script.
# Checks all configured Lambda endpoints and exits with status code
# indicating overall health (0 = all passed, 1 = one or more failed).
main() {
    log_info "Starting health check for Chicken Coop API endpoints"

    local failed=0

    # Get endpoint URLs
    STATUS_URL=$(get_api_url "status")
    SENSOR_URL=$(get_api_url "sensorData")
    VIDEOS_URL=$(get_api_url "videos")

    # Check status endpoint
    if ! check_endpoint "status" "$STATUS_URL"; then
        failed=1
    fi

    # Check sensorData endpoint
    if ! check_endpoint "sensorData" "$SENSOR_URL"; then
        failed=1
    fi

    # Check videos endpoint
    if ! check_endpoint "videos" "$VIDEOS_URL"; then
        failed=1
    fi

    if [ $failed -eq 0 ]; then
        log_info "All health checks passed"
        exit 0
    else
        log_error "One or more health checks failed"
        exit 1
    fi
}

main "$@"
