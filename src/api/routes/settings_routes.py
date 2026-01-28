"""
Settings Routes for Chicken Coop API
=====================================

Provides endpoints for user settings management including:
- Temperature unit preference (Fahrenheit/Celsius)
- Alert threshold configuration
- Notification preferences
- Reset to defaults functionality
"""

from flask import Blueprint, jsonify, request

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')

# Default settings values
DEFAULT_SETTINGS = {
    'temperature_unit': 'F',
    'thresholds': {
        'temperature_min': 32,
        'temperature_max': 95,
        'humidity_min': 30,
        'humidity_max': 80
    },
    'notifications': {
        'email_enabled': True,
        'temperature_alerts': True,
        'humidity_alerts': True,
        'system_alerts': True
    }
}

# In-memory storage for settings (in production would use database)
_settings = {
    'temperature_unit': DEFAULT_SETTINGS['temperature_unit'],
    'thresholds': DEFAULT_SETTINGS['thresholds'].copy(),
    'notifications': DEFAULT_SETTINGS['notifications'].copy()
}


def reset_settings_to_defaults():
    """Reset all settings to their default values.

    This function is primarily used for testing to ensure a clean state.
    Resets temperature unit, thresholds, and notification preferences.
    """
    _settings['temperature_unit'] = DEFAULT_SETTINGS['temperature_unit']
    _settings['thresholds'] = DEFAULT_SETTINGS['thresholds'].copy()
    _settings['notifications'] = DEFAULT_SETTINGS['notifications'].copy()


# =============================================================================
# Temperature Unit Endpoints
# =============================================================================

@settings_bp.route('/temperature-unit', methods=['GET'])
def get_temperature_unit():
    """Get current temperature unit preference."""
    return jsonify({'unit': _settings['temperature_unit']})


@settings_bp.route('/temperature-unit', methods=['PUT'])
def set_temperature_unit():
    """Set temperature unit preference."""
    data = request.get_json() or {}
    unit = data.get('unit')

    if unit not in ('F', 'C'):
        return jsonify({'error': 'Invalid unit. Must be F or C'}), 400

    _settings['temperature_unit'] = unit
    return jsonify({'unit': _settings['temperature_unit']})


# =============================================================================
# Threshold Endpoints
# =============================================================================

@settings_bp.route('/thresholds', methods=['GET'])
def get_thresholds():
    """Get current alert thresholds."""
    return jsonify(_settings['thresholds'])


@settings_bp.route('/thresholds', methods=['PUT'])
def set_thresholds():
    """Set alert thresholds."""
    data = request.get_json() or {}

    temp_min = data.get('temperature_min', _settings['thresholds']['temperature_min'])
    temp_max = data.get('temperature_max', _settings['thresholds']['temperature_max'])
    humidity_min = data.get('humidity_min', _settings['thresholds']['humidity_min'])
    humidity_max = data.get('humidity_max', _settings['thresholds']['humidity_max'])

    # Validate temperature min < max
    if temp_min >= temp_max:
        return jsonify({'error': 'temperature_min must be less than temperature_max'}), 400

    # Validate humidity min < max
    if humidity_min >= humidity_max:
        return jsonify({'error': 'humidity_min must be less than humidity_max'}), 400

    # Validate humidity range 0-100
    if humidity_min < 0 or humidity_max > 100:
        return jsonify({'error': 'Humidity must be between 0 and 100'}), 400

    _settings['thresholds']['temperature_min'] = temp_min
    _settings['thresholds']['temperature_max'] = temp_max
    _settings['thresholds']['humidity_min'] = humidity_min
    _settings['thresholds']['humidity_max'] = humidity_max

    return jsonify(_settings['thresholds'])


# =============================================================================
# Notification Endpoints
# =============================================================================

@settings_bp.route('/notifications', methods=['GET'])
def get_notifications():
    """Get current notification preferences."""
    return jsonify(_settings['notifications'])


@settings_bp.route('/notifications', methods=['PUT'])
def set_notifications():
    """Set notification preferences."""
    data = request.get_json() or {}

    if 'email_enabled' in data:
        _settings['notifications']['email_enabled'] = data['email_enabled']
    if 'temperature_alerts' in data:
        _settings['notifications']['temperature_alerts'] = data['temperature_alerts']
    if 'humidity_alerts' in data:
        _settings['notifications']['humidity_alerts'] = data['humidity_alerts']
    if 'system_alerts' in data:
        _settings['notifications']['system_alerts'] = data['system_alerts']

    return jsonify(_settings['notifications'])


# =============================================================================
# Reset Endpoints
# =============================================================================

@settings_bp.route('/reset', methods=['POST'])
def reset_settings():
    """Reset all settings to defaults."""
    _settings['temperature_unit'] = DEFAULT_SETTINGS['temperature_unit']
    _settings['thresholds'] = DEFAULT_SETTINGS['thresholds'].copy()
    _settings['notifications'] = DEFAULT_SETTINGS['notifications'].copy()

    return jsonify({'success': True})
