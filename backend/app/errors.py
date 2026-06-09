from flask import jsonify


def register_error_handlers(app):
    """
    Register global JSON error handlers so every error response —
    including Flask internals — returns consistent JSON, not HTML.
    """

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"success": False, "error": "Bad request", "message": str(e)}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"success": False, "error": "Unauthorized", "message": str(e)}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"success": False, "error": "Forbidden", "message": str(e)}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "error": "Not found", "message": str(e)}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({
            "success": False,
            "error": "Method not allowed",
            "message": str(e),
        }), 405

    @app.errorhandler(409)
    def conflict(e):
        return jsonify({"success": False, "error": "Conflict", "message": str(e)}), 409

    @app.errorhandler(422)
    def unprocessable(e):
        return jsonify({
            "success": False,
            "error": "Unprocessable entity",
            "message": str(e),
        }), 422

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again.",
        }), 500