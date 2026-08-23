def register_routes(app):
    """Register all route blueprints with the Flask app."""
    from app.routes.tests import tests_bp
    app.register_blueprint(tests_bp)
