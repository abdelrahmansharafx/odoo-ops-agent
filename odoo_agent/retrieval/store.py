"""Chunking and Chroma search over the markdown business-process docs (persisted on disk)."""
from __future__ import annotations

import re
from pathlib import Path

import chromadb

ROOT = Path(__file__).resolve().parent.parent.parent
DOCS_DIR = ROOT / "knowledge"
PERSIST_DIR = ROOT / ".chroma"
TOP_K = 3


def chunk_markdown(path: Path) -> list[tuple[str, str]]:
    """Split a doc into (chunk_id, text) pieces at '## ' headings, each prefixed with the doc title."""
    text = path.read_text(encoding="utf-8").strip()
    title = text.splitlines()[0].lstrip("# ").strip()
    parts = re.split(r"\n(?=## )", text)
    return [
        (f"{path.stem}:{i}", part if i == 0 else f"{title}\n{part}")
        for i, part in enumerate(parts)
        if part.strip()
    ]


class DocStore:
    def __init__(self, docs_dir: Path = DOCS_DIR, persist_dir: Path | None = PERSIST_DIR, embedding_function=None):
        client = chromadb.PersistentClient(str(persist_dir)) if persist_dir else chromadb.EphemeralClient()
        kwargs = {"embedding_function": embedding_function} if embedding_function else {}
        # Default embedder is Chroma's bundled ONNX MiniLM: local, no API key needed.
        self._col = client.get_or_create_collection("process_docs", **kwargs)
        self._docs_dir = docs_dir
        self.reindex()

    def reindex(self) -> int:
        """Rebuild the collection from disk so edits to /knowledge are always picked up."""
        existing = self._col.get()["ids"]
        if existing:
            self._col.delete(ids=existing)
        ids, texts, metas = [], [], []
        for path in sorted(self._docs_dir.glob("*.md")):
            for chunk_id, text in chunk_markdown(path):
                ids.append(chunk_id)
                texts.append(text)
                metas.append({"source": path.name})
        if ids:
            self._col.add(ids=ids, documents=texts, metadatas=metas)
        return len(ids)

    def search(self, query: str, k: int = TOP_K) -> list[dict]:
        res = self._col.query(query_texts=[query], n_results=min(k, max(self._col.count(), 1)))
        return [
            {"source": m["source"], "text": d}
            for d, m in zip(res["documents"][0], res["metadatas"][0])
        ]

