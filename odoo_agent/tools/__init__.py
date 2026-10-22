"""Agent tools. Re-exports every tool (and its test hooks) so `from odoo_agent.tools import ...` keeps working."""
from .knowledge_tools import get_store, search_process_docs, set_store
from .odoo_tools import (
    DATA_TOOLS,
    MAX_ROWS,
    get_client,
    get_customer_profile,
    get_pipeline_summary,
    search_leads,
    search_sales_orders,
    set_client,
)

__all__ = [
    "DATA_TOOLS", "MAX_ROWS", "get_client", "get_customer_profile", "get_pipeline_summary", "get_store",
    "search_leads", "search_process_docs", "search_sales_orders", "set_client", "set_store",
]
