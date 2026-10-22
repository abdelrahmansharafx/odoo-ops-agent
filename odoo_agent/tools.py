"""LangChain tools over Odoo. All read-only; every tool returns JSON-serialisable data."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Literal, Optional

from langchain_core.tools import tool

from .odoo_client import OdooClient

MAX_ROWS = 25

_client: OdooClient | None = None


def set_client(client: OdooClient | None) -> None:
    """Inject a client (used by tests); None resets to the env-configured default."""
    global _client
    _client = client


def get_client() -> OdooClient:
    global _client
    if _client is None:
        _client = OdooClient.from_env()
    return _client


def _parse_date(value: str, label: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{label} must be an ISO date (YYYY-MM-DD), got {value!r}") from None


def _date_domain(field: str, date_from: Optional[str], date_to: Optional[str]) -> list:
    domain = []
    if date_from:
        domain.append((field, ">=", f"{_parse_date(date_from, 'date_from')} 00:00:00"))
    if date_to:  # inclusive: strictly before the next day
        domain.append((field, "<", f"{_parse_date(date_to, 'date_to') + timedelta(days=1)} 00:00:00"))
    return domain


def _name(value) -> Optional[str]:
    """Many2one values arrive as [id, name] or False."""
    return value[1] if value else None


def _cap(rows: list[dict]) -> dict:
    return {"total": len(rows), "truncated": len(rows) > MAX_ROWS, "rows": rows[:MAX_ROWS]}


@tool
def search_leads(
    stage: Optional[str] = None,
    salesperson: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> dict:
    """Search CRM leads/opportunities. Returns the total count and up to 25 rows.

    Args:
        stage: Pipeline stage name, partial match (e.g. "Qualified", "Proposition", "Won", "New").
        salesperson: Salesperson name, partial match.
        date_from: Only leads created on/after this date (YYYY-MM-DD).
        date_to: Only leads created on/before this date (YYYY-MM-DD).
    """
    domain: list = _date_domain("create_date", date_from, date_to)
    if stage:
        domain.append(("stage_id.name", "ilike", stage))
    if salesperson:
        domain.append(("user_id.name", "ilike", salesperson))
    rows = get_client().search_read(
        "crm.lead",
        domain,
        ["name", "partner_id", "stage_id", "user_id", "expected_revenue", "create_date"],
        order="create_date desc",
    )
    return _cap([
        {
            "name": r["name"],
            "customer": _name(r["partner_id"]),
            "stage": _name(r["stage_id"]),
            "salesperson": _name(r["user_id"]),
            "expected_revenue": r["expected_revenue"],
            "created": r["create_date"],
        }
        for r in rows
    ])


@tool
def get_pipeline_summary(group_by: Literal["stage", "salesperson"]) -> dict:
    """Summarise the active CRM pipeline: lead count and total expected revenue per group.

    Args:
        group_by: "stage" to group by pipeline stage, "salesperson" to group by owner.
    """
    field = {"stage": "stage_id", "salesperson": "user_id"}[group_by]
    rows = get_client().read_group("crm.lead", [], ["expected_revenue:sum"], [field])
    groups = [
        {
            "group": _name(r[field]) or "Unassigned",
            "count": r["__count"],
            "expected_revenue": r.get("expected_revenue") or 0,
        }
        for r in rows
    ]
    return {
        "group_by": group_by,
        "groups": groups,
        "total_count": sum(g["count"] for g in groups),
        "total_expected_revenue": sum(g["expected_revenue"] for g in groups),
    }


@tool
def search_sales_orders(
    state: Optional[Literal["draft", "sent", "sale", "cancel"]] = None,
    customer: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> dict:
    """Search sales orders/quotations. Returns the total count, total amount and up to 25 rows.

    Args:
        state: "draft" (quotation), "sent" (quotation sent), "sale" (confirmed order), "cancel".
        customer: Customer name, partial match.
        date_from: Only orders dated on/after this date (YYYY-MM-DD).
        date_to: Only orders dated on/before this date (YYYY-MM-DD).
    """
    domain: list = _date_domain("date_order", date_from, date_to)
    if state:
        domain.append(("state", "=", state))
    if customer:
        domain.append(("partner_id.name", "ilike", customer))
    rows = get_client().search_read(
        "sale.order",
        domain,
        ["name", "partner_id", "state", "amount_total", "date_order", "user_id"],
        order="date_order desc",
    )
    result = _cap([
        {
            "order": r["name"],
            "customer": _name(r["partner_id"]),
            "state": r["state"],
            "amount_total": r["amount_total"],
            "date": r["date_order"],
            "salesperson": _name(r["user_id"]),
        }
        for r in rows
    ])
    result["total_amount"] = round(sum(r["amount_total"] for r in rows), 2)
    return result


@tool
def get_customer_profile(name: str) -> dict:
    """Get a customer's contact details, open leads and sales orders (exact order_count plus the 10 latest).

    Args:
        name: Customer/company name, partial match (the first match is used).
    """
    client = get_client()
    partners = client.search_read(
        "res.partner",
        [("name", "ilike", name)],
        ["name", "email", "phone", "city", "country_id", "is_company"],
        limit=1,
        order="is_company desc, id",
    )
    if not partners:
        return {"found": False, "name": name}
    p = partners[0]
    leads = client.search_read(
        "crm.lead",
        [("partner_id", "=", p["id"]), ("stage_id.is_won", "=", False)],
        ["name", "stage_id", "expected_revenue"],
    )
    orders = client.search_read(
        "sale.order",
        [("partner_id", "=", p["id"])],
        ["name", "state", "amount_total", "date_order"],
        order="date_order desc",
    )
    return {
        "found": True,
        "contact": {
            "name": p["name"],
            "email": p["email"] or None,
            "phone": p["phone"] or None,
            "city": p["city"] or None,
            "country": _name(p["country_id"]),
            "is_company": p["is_company"],
        },
        "open_leads": [
            {"name": l["name"], "stage": _name(l["stage_id"]), "expected_revenue": l["expected_revenue"]}
            for l in leads
        ],
        "order_count": len(orders),  # exact total; `orders` below lists only the latest 10
        "orders": [
            {"order": o["name"], "state": o["state"], "amount_total": o["amount_total"], "date": o["date_order"]}
            for o in orders[:10]
        ],
    }


DATA_TOOLS = [search_leads, get_pipeline_summary, search_sales_orders, get_customer_profile]
