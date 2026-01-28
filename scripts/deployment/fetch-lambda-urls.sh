#!/bin/bash
#
# Fetch Lambda URLs from CloudFormation and update amplify_outputs.json
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
AMPLIFY_OUTPUTS="$PROJECT_ROOT/webapp/amplify_outputs.json"
STACK_NAME="${STACK_NAME:-chickencoop-stack}"

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

# Retrieve a Lambda function URL from CloudFormation stack outputs.
# Arguments:
#   $1 - CloudFormation output key name (e.g., "StatusFunctionUrl")
# Returns:
#   The URL string if found, empty string otherwise
get_lambda_url() {
    local output_key=$1
    aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --query "Stacks[0].Outputs[?OutputKey=='${output_key}'].OutputValue" \
        --output text 2>/dev/null || echo ""
}

# Main entry point for Lambda URL fetching script.
# Fetches Lambda function URLs from CloudFormation and updates amplify_outputs.json.
# Creates a backup of the existing file before modification.
main() {
    log_info "Fetching Lambda URLs from CloudFormation stack: $STACK_NAME"

    # Fetch URLs from CloudFormation
    STATUS_URL=$(get_lambda_url "StatusFunctionUrl")
    SENSOR_URL=$(get_lambda_url "SensorDataFunctionUrl")
    VIDEOS_URL=$(get_lambda_url "VideosFunctionUrl")

    log_info "Status URL: $STATUS_URL"
    log_info "SensorData URL: $SENSOR_URL"
    log_info "Videos URL: $VIDEOS_URL"

    # Create backup of existing amplify_outputs.json
    if [ -f "$AMPLIFY_OUTPUTS" ]; then
        log_info "Creating backup of amplify_outputs.json"
        cp "$AMPLIFY_OUTPUTS" "${AMPLIFY_OUTPUTS}.bak"
    fi

    # Update amplify_outputs.json with new URLs
    if [ -f "$AMPLIFY_OUTPUTS" ]; then
        log_info "Updating amplify_outputs.json with Lambda URLs"

        # Add or update custom section with Lambda URLs
        jq --arg status "$STATUS_URL" \
           --arg sensor "$SENSOR_URL" \
           --arg videos "$VIDEOS_URL" \
           '.custom = (.custom // {}) | .custom.statusUrl = $status | .custom.sensorDataUrl = $sensor | .custom.videosUrl = $videos' \
           "$AMPLIFY_OUTPUTS" > "${AMPLIFY_OUTPUTS}.tmp" && mv "${AMPLIFY_OUTPUTS}.tmp" "$AMPLIFY_OUTPUTS"

        log_info "amplify_outputs.json updated successfully"
    else
        log_error "amplify_outputs.json not found at $AMPLIFY_OUTPUTS"
        exit 1
    fi
}

main "$@"
