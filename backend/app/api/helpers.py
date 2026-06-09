from flask import jsonify, request


def success(data=None, message=None, status=200):
    """Standard success envelope."""
    body = {"success": True}
    if message:
        body["message"] = message
    if data is not None:
        body["data"] = data
    return jsonify(body), status


def created(data=None, message="Resource created"):
    return success(data=data, message=message, status=201)


def error(message, status=400, details=None):
    """Standard error envelope."""
    body = {"success": False, "error": message}
    if details:
        body["details"] = details
    return jsonify(body), status


def not_found(resource="Resource"):
    return error(f"{resource} not found", 404)


def forbidden(message="You do not have permission to perform this action"):
    return error(message, 403)


def paginate(query, schema_fn):
    """
    Apply page/per_page query params to a SQLAlchemy query and
    return a paginated response dict.
    Usage: return success(paginate(Project.query, serialize_project))
    """
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        "items": [schema_fn(item) for item in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
    }