"""API routes module."""
from src.api.routes.admin_routes import admin_bp
from src.api.routes.alert_routes import alert_bp
from src.api.routes.headcount_routes import headcount_bp

__all__ = ['admin_bp', 'alert_bp', 'headcount_bp']
