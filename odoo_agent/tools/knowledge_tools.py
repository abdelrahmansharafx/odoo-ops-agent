"""LangChain tool over the process docs (RAG)."""
from __future__ import annotations

from langchain_core.tools import tool

from ..retrieval.store import DocStore

_store: DocStore | None = None


def set_store(store: DocStore | None) -> None:
    global _store
    _store = store


def get_store() -> DocStore:
    global _store
    if _store is None:
        _store = DocStore()
    return _store


@tool
def search_process_docs(query: str) -> list[dict]:
    """Search internal business-process documentation (policies and procedures).

    Use for "how/what is the policy/process" questions: lead routing, sales stages,
    refunds, discount approvals, quotation-to-order steps, customer data handling.
    Does NOT contain live CRM or sales data. Returns the top matching passages with their source file.

    Args:
        query: Natural-language description of what to look up.
    """
    return get_store().search(query)
