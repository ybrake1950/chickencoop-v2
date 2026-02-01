"""
Chicken Coop v2 — Application Entry Point
==========================================

The systemd service runs: python -m src.main
"""

import logging
import os
import signal
import sys

from flask import Blueprint, Flask, jsonify


def create_app(testing=False):
    """Flask application factory.

    Args:
        testing: If True, configure app for testing mode.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)

    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key and not testing:
        logging.getLogger('chickencoop').warning(
            'SECRET_KEY not set; using generated key (sessions will not persist across restarts)'
        )
        import secrets
        secret_key = secrets.token_hex(32)
    app.config['SECRET_KEY'] = secret_key or 'test-secret-key'
    app.config['TESTING'] = testing

    # Register route blueprints
    from src.api.routes import register_all_routes
    register_all_routes(app)

    # Register diagnostics blueprint (not in register_all_routes)
    from src.api.routes.diagnostics_routes import diagnostics_bp
    if 'diagnostics' not in app.blueprints:
        app.register_blueprint(diagnostics_bp)

    # Register sensors and videos routes (these use register_routes(app) pattern)
    from src.api.routes.sensors import register_routes as register_sensor_routes
    register_sensor_routes(app)
    app.register_blueprint(Blueprint('sensors', __name__))

    from src.api.routes.videos import register_routes as register_video_routes
    register_video_routes(app)
    app.register_blueprint(Blueprint('videos', __name__))

    # Health check endpoint
    @app.route('/health')
    def health():
        """Return a JSON health check response for load balancer probes."""
        return jsonify({'status': 'ok'})

    return app


def main():
    """Initialize logging, register signal handlers, and start the Flask server.

    Configures structured logging, installs SIGTERM/SIGINT handlers for
    graceful shutdown, and runs the Flask development server. Host and port
    are configurable via FLASK_HOST and FLASK_PORT environment variables.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    )
    logger = logging.getLogger('chickencoop')

    def handle_sigterm(signum, frame):
        logger.info('Received SIGTERM, shutting down...')
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_sigterm)
    signal.signal(signal.SIGINT, signal.default_int_handler)

    app = create_app()
    logger.info('Starting Chicken Coop application')
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', '5000'))
    app.run(host=host, port=port)


if __name__ == '__main__':
    main()
