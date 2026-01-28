"""API routes module."""
from src.api.routes.admin_routes import admin_bp
from src.api.routes.alert_routes import alert_bp
from src.api.routes.headcount_routes import headcount_bp
from src.api.routes.dashboard_routes import dashboard_bp
from src.api.routes.settings_routes import settings_bp
from src.api.routes.chickens import chickens_bp
from src.api.routes.auth_routes import auth_bp
from src.api.routes.sns_routes import sns_bp
from src.api.routes.page_routes import page_bp

__all__ = [
    'admin_bp',
    'alert_bp',
    'headcount_bp',
    'dashboard_bp',
    'settings_bp',
    'chickens_bp',
    'auth_bp',
    'sns_bp',
    'page_bp',
    'register_all_routes'
]


def register_all_routes(app):
    """Register all route blueprints with the Flask application.

    Args:
        app: The Flask application instance to register routes with.

    Note:
        This function safely skips blueprints that are already registered.
    """
    blueprints = [
        admin_bp,
        alert_bp,
        headcount_bp,
        dashboard_bp,
        settings_bp,
        chickens_bp,
        auth_bp,
        sns_bp,
        page_bp
    ]

    registered_names = set(app.blueprints.keys())

    for bp in blueprints:
        if bp.name not in registered_names:
            app.register_blueprint(bp)
