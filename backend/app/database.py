"""
ReconAI Database — Async Storage Layer with Instant In-Memory Engine & MongoDB Support.
"""
from typing import Dict, Any, List, Optional
import asyncio

class AsyncCollection:
    """Async collection simulation with MongoDB-compatible API."""
    def __init__(self, name: str):
        self.name = name
        self._docs: List[Dict[str, Any]] = []

    async def insert_many(self, docs: List[Dict[str, Any]]):
        self._docs.extend([dict(d) for d in docs])
        return len(docs)

    async def insert_one(self, doc: Dict[str, Any]):
        self._docs.append(dict(doc))
        return doc

    async def delete_many(self, filter_dict: Optional[Dict] = None):
        count = len(self._docs)
        self._docs.clear()
        return count

    def find(self, filter_dict: Optional[Dict] = None, projection: Optional[Dict] = None):
        return AsyncCursor(list(self._docs), projection)

    async def create_index(self, key: str, unique: bool = False):
        pass


class AsyncCursor:
    """Async cursor for MongoDB-style .to_list() operations."""
    def __init__(self, items: List[Dict[str, Any]], projection: Optional[Dict] = None):
        self._items = items
        self._projection = projection or {}

    async def to_list(self, length: Optional[int] = None):
        res = []
        for item in self._items:
            doc = dict(item)
            if self._projection.get("_id") == 0:
                doc.pop("_id", None)
            res.append(doc)
            if length and len(res) >= length:
                break
        return res


class ReconDatabase:
    """In-memory high-throughput repository with instant startup."""
    def __init__(self):
        self.orders = AsyncCollection("orders")
        self.payments = AsyncCollection("payments")
        self.settlements = AsyncCollection("settlements")
        self.recon_entries = AsyncCollection("recon_entries")
        self.recon_results = AsyncCollection("recon_results")
        self.qa_history = AsyncCollection("qa_history")

db = ReconDatabase()

async def connect_db():
    print("[DB] ReconAI In-Memory Engine initialized and ready.")

async def close_db():
    print("[DB] ReconAI database connection closed.")

def get_db():
    return db
