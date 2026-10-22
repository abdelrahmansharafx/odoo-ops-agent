"""Thin, read-only XML-RPC wrapper around Odoo's external API."""
from __future__ import annotations

import os
import xmlrpc.client
from typing import Any, Callable

# Only these ORM methods can ever be sent to the server.
READ_ONLY_METHODS = frozenset({"search_read", "read_group"})


class OdooError(RuntimeError):
    pass


class OdooClient:
    def __init__(
        self,
        url: str,
        db: str,
        user: str,
        password: str,
        proxy_factory: Callable[[str], Any] = xmlrpc.client.ServerProxy,
    ) -> None:
        base = url.rstrip("/")
        self._db, self._user, self._password = db, user, password
        self._common = proxy_factory(f"{base}/xmlrpc/2/common")
        self._models = proxy_factory(f"{base}/xmlrpc/2/object")
        self._uid: int | None = None

    @classmethod
    def from_env(cls) -> "OdooClient":
        return cls(
            os.getenv("ODOO_URL", "http://localhost:8069"),
            os.getenv("ODOO_DB", "odoo"),
            os.getenv("ODOO_USER", "admin"),
            os.getenv("ODOO_PASSWORD", "admin"),
        )

    @property
    def uid(self) -> int:
        if self._uid is None:
            uid = self._common.authenticate(self._db, self._user, self._password, {})
            if not uid:
                raise OdooError("Odoo authentication failed (check ODOO_* settings)")
            self._uid = uid
        return self._uid

    def _call(self, model: str, method: str, *args: Any, **kwargs: Any) -> Any:
        if method not in READ_ONLY_METHODS:
            raise OdooError(f"Method {method!r} is not allowed: client is read-only")
        try:
            return self._models.execute_kw(
                self._db, self.uid, self._password, model, method, list(args), kwargs
            )
        except xmlrpc.client.Fault as exc:
            raise OdooError(f"Odoo fault on {model}.{method}: {exc.faultString}") from exc

    def search_read(
        self,
        model: str,
        domain: list | None = None,
        fields: list[str] | None = None,
        limit: int | None = None,
        order: str | None = None,
    ) -> list[dict]:
        kwargs: dict[str, Any] = {"fields": fields or []}
        if limit is not None:
            kwargs["limit"] = limit
        if order:
            kwargs["order"] = order
        return self._call(model, "search_read", domain or [], **kwargs)

    def read_group(
        self,
        model: str,
        domain: list | None,
        fields: list[str],
        groupby: list[str],
    ) -> list[dict]:
        """Grouped aggregation; each row carries `__count` plus aggregated fields."""
        return self._call(
            model, "read_group", domain or [], fields, groupby, lazy=False
        )
