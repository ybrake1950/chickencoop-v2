"""Authentication decorators."""

from functools import wraps
from flask import session, abort


def login_required(f):
    """Decorator to require authentication for a route."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            abort(401)
        return f(*args, **kwargs)

    return decorated_function
