from pathlib import Path

import pytest
from chromadb import Documents, EmbeddingFunction, Embeddings

from odoo_agent import tools as rag
from odoo_agent.retrieval import store as retrieval_store

VOCAB = ["refund", "credit", "discount", "stage", "routing", "lead", "approve", "days"]


class BagOfWords(EmbeddingFunction):
    """Deterministic offline embedder so tests never download a model."""

    def __init__(self): ...

    def __call__(self, input: Documents) -> Embeddings:
        return [[float(t.lower().count(w)) for w in VOCAB] + [0.01] for t in input]

    @staticmethod
    def name() -> str:
        return "bow"

    def get_config(self):
        return {}

    @staticmethod
    def build_from_config(config):
        return BagOfWords()


@pytest.fixture
def store(tmp_path: Path):
    (tmp_path / "refund.md").write_text("# Refund Policy\n\nRefund within 30 days.\n\n## Approval\nApprove refund above 500.")
    (tmp_path / "stages.md").write_text("# Sales Stages\n\nEach lead sits in one stage.")
    s = retrieval_store.DocStore(tmp_path, persist_dir=None, embedding_function=BagOfWords())
    rag.set_store(s)
    yield s
    rag.set_store(None)


def test_chunking_splits_on_h2_and_keeps_title(tmp_path):
    p = tmp_path / "a.md"
    p.write_text("# Title\n\nintro\n\n## Part\nbody")
    chunks = retrieval_store.chunk_markdown(p)
    assert [c[0] for c in chunks] == ["a:0", "a:1"]
    assert chunks[1][1].startswith("Title\n## Part")


def test_search_returns_relevant_source(store):
    hits = store.search("refund approve", k=1)
    assert hits[0]["source"] == "refund.md"


def test_reindex_picks_up_new_files(store, tmp_path):
    (tmp_path / "disc.md").write_text("# Discount Policy\n\nDiscount needs approve.")
    assert store.reindex() == 4
    assert any(h["source"] == "disc.md" for h in store.search("discount", k=1))


def test_tool_returns_passages(store):
    out = rag.search_process_docs.invoke({"query": "stage of a lead"})
    assert out and {"source", "text"} <= out[0].keys()


def test_real_docs_chunk_cleanly():
    for p in retrieval_store.DOCS_DIR.glob("*.md"):
        assert retrieval_store.chunk_markdown(p)
