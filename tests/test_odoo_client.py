import xmlrpc.client
from unittest.mock import MagicMock

import pytest

from odoo_agent.odoo_client import OdooClient, OdooError


@pytest.fixture
def proxies():
    common, models = MagicMock(), MagicMock()
    common.authenticate.return_value = 7

    def factory(url):
        return common if url.endswith("/common") else models

    return common, models, factory


def make(factory):
    return OdooClient("http://odoo:8069/", "db", "u", "p", proxy_factory=factory)


def test_search_read_authenticates_once_and_passes_args(proxies):
    common, models, factory = proxies
    models.execute_kw.return_value = [{"id": 1}]
    c = make(factory)
    assert c.search_read("crm.lead", [("active", "=", True)], ["name"], limit=5, order="id") == [{"id": 1}]
    c.search_read("crm.lead")
    common.authenticate.assert_called_once_with("db", "u", "p", {})
    first = models.execute_kw.call_args_list[0].args
    assert first == ("db", 7, "p", "crm.lead", "search_read", [[("active", "=", True)]], {"fields": ["name"], "limit": 5, "order": "id"})


def test_read_group_is_non_lazy(proxies):
    _, models, factory = proxies
    models.execute_kw.return_value = []
    make(factory).read_group("crm.lead", [], ["expected_revenue:sum"], ["stage_id"])
    args = models.execute_kw.call_args.args
    assert args[4] == "read_group"
    assert models.execute_kw.call_args.args[6] == {"lazy": False}


def test_auth_failure(proxies):
    common, _, factory = proxies
    common.authenticate.return_value = False
    with pytest.raises(OdooError, match="authentication"):
        make(factory).search_read("crm.lead")


@pytest.mark.parametrize("method", ["write", "create", "unlink", "execute"])
def test_write_methods_are_blocked(proxies, method):
    _, models, factory = proxies
    with pytest.raises(OdooError, match="read-only"):
        make(factory)._call("crm.lead", method, [1], {})
    models.execute_kw.assert_not_called()


def test_fault_is_wrapped(proxies):
    _, models, factory = proxies
    models.execute_kw.side_effect = xmlrpc.client.Fault(1, "boom")
    with pytest.raises(OdooError, match="boom"):
        make(factory).search_read("crm.lead")
