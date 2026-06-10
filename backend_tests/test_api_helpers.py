from types import SimpleNamespace

from app.api.helpers import created, error, forbidden, not_found, paginate, success


class _FakeQuery:
    def __init__(self, items, total=0, pages=0, has_next=False, has_prev=False):
        self._items = items
        self._total = total
        self._pages = pages
        self._has_next = has_next
        self._has_prev = has_prev

    def paginate(self, page, per_page, error_out):
        assert error_out is False
        return SimpleNamespace(
            items=self._items,
            page=page,
            total=self._total,
            pages=self._pages,
            has_next=self._has_next,
            has_prev=self._has_prev,
        )


def test_success_and_created_envelopes(app):
    with app.test_request_context("/"):
        body, status = success({"k": "v"}, message="ok")
        assert status == 200
        assert body.get_json() == {
            "success": True,
            "message": "ok",
            "data": {"k": "v"},
        }

        body, status = created(message="made")
        assert status == 201
        assert body.get_json() == {
            "success": True,
            "message": "made",
        }


def test_error_not_found_and_forbidden_envelopes(app):
    with app.test_request_context("/"):
        body, status = error("bad", details={"field": "name"})
        assert status == 400
        assert body.get_json() == {
            "success": False,
            "error": "bad",
            "details": {"field": "name"},
        }

        body, status = not_found("Project")
        assert status == 404
        assert body.get_json()["error"] == "Project not found"

        body, status = forbidden("Nope")
        assert status == 403
        assert body.get_json()["error"] == "Nope"


def test_paginate_returns_items_and_metadata(app):
    with app.test_request_context("/?page=2&per_page=200"):
        query = _FakeQuery(
            items=[{"id": 1}, {"id": 2}],
            total=32,
            pages=16,
            has_next=True,
            has_prev=True,
        )

        payload = paginate(query, lambda i: i)

    assert payload["items"] == [{"id": 1}, {"id": 2}]
    assert payload["pagination"] == {
        "page": 2,
        "per_page": 100,
        "total": 32,
        "pages": 16,
        "has_next": True,
        "has_prev": True,
    }
