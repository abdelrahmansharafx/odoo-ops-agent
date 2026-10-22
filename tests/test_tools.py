from unittest.mock import MagicMock

import pytest

from odoo_agent import tools


@pytest.fixture
def client():
    c = MagicMock()
    tools.set_client(c)
    yield c
    tools.set_client(None)


def test_search_leads_builds_domain_and_shapes_rows(client):
    client.search_read.return_value = [
        {"name": "Big deal", "partner_id": [1, "Acme"], "stage_id": [2, "Qualified"],
         "user_id": False, "expected_revenue": 500.0, "create_date": "2026-01-02 10:00:00"}
    ]
    out = tools.search_leads.invoke({"stage": "Qualified", "date_from": "2026-01-01", "date_to": "2026-01-31"})
    domain = client.search_read.call_args.args[1]
    assert ("stage_id.name", "ilike", "Qualified") in domain
    assert ("create_date", ">=", "2026-01-01 00:00:00") in domain
    assert ("create_date", "<", "2026-02-01 00:00:00") in domain  # date_to is inclusive
    assert out["total"] == 1 and out["rows"][0]["salesperson"] is None
    assert out["rows"][0]["customer"] == "Acme"


def test_search_leads_truncates(client):
    client.search_read.return_value = [
        {"name": str(i), "partner_id": False, "stage_id": False, "user_id": False,
         "expected_revenue": 0, "create_date": "x"} for i in range(40)
    ]
    out = tools.search_leads.invoke({})
    assert out["total"] == 40 and out["truncated"] and len(out["rows"]) == tools.MAX_ROWS


def test_bad_date_is_rejected(client):
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        tools.search_leads.invoke({"date_from": "last week"})


def test_pipeline_summary_by_stage(client):
    client.read_group.return_value = [
        {"stage_id": [1, "New"], "__count": 4, "expected_revenue": 100.0},
        {"stage_id": [2, "Qualified"], "__count": 3, "expected_revenue": 250.0},
    ]
    out = tools.get_pipeline_summary.invoke({"group_by": "stage"})
    assert client.read_group.call_args.args[3] == ["stage_id"]
    assert out["total_count"] == 7 and out["total_expected_revenue"] == 350.0
    assert out["groups"][1] == {"group": "Qualified", "count": 3, "expected_revenue": 250.0}


def test_pipeline_summary_unassigned_salesperson(client):
    client.read_group.return_value = [{"user_id": False, "__count": 2, "expected_revenue": 0}]
    out = tools.get_pipeline_summary.invoke({"group_by": "salesperson"})
    assert out["groups"][0]["group"] == "Unassigned"


def test_pipeline_summary_rejects_unknown_group(client):
    with pytest.raises(Exception):
        tools.get_pipeline_summary.invoke({"group_by": "country"})


def test_sales_orders_total_amount(client):
    client.search_read.return_value = [
        {"name": "S1", "partner_id": [1, "Acme"], "state": "sale", "amount_total": 100.5,
         "date_order": "d", "user_id": [2, "Mitchell"]},
        {"name": "S2", "partner_id": [1, "Acme"], "state": "sale", "amount_total": 50.25,
         "date_order": "d", "user_id": False},
    ]
    out = tools.search_sales_orders.invoke({"state": "sale", "customer": "Acme"})
    domain = client.search_read.call_args.args[1]
    assert ("state", "=", "sale") in domain and ("partner_id.name", "ilike", "Acme") in domain
    assert out["total"] == 2 and out["total_amount"] == 150.75


def test_customer_profile_found(client):
    client.search_read.side_effect = [
        [{"id": 9, "name": "Acme", "email": "a@x.com", "phone": False, "city": "Paris",
          "country_id": [1, "France"], "is_company": True}],
        [{"name": "Lead A", "stage_id": [1, "New"], "expected_revenue": 10}],
        [{"name": "S1", "state": "sale", "amount_total": 5, "date_order": "d"}],
    ]
    out = tools.get_customer_profile.invoke({"name": "acme"})
    assert out["found"] and out["contact"]["country"] == "France" and out["contact"]["phone"] is None
    assert out["open_leads"][0]["stage"] == "New" and out["orders"][0]["order"] == "S1"


def test_customer_profile_not_found(client):
    client.search_read.return_value = []
    assert tools.get_customer_profile.invoke({"name": "nobody"}) == {"found": False, "name": "nobody"}
    assert client.search_read.call_count == 1


def test_tools_expose_docstrings_and_typed_schema():
    for t in tools.DATA_TOOLS:
        assert t.description and t.args
