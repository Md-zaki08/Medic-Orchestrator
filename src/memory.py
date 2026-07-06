import sqlite3
import json
import math
import structlog
from typing import List, Dict, Any, Optional

logger = structlog.get_logger()


class VectorMemoryStore:
    def __init__(self, use_postgres: bool = False, dsn: Optional[str] = None):
        self.use_postgres = use_postgres
        self.dsn = dsn
        self.sqlite_path = "memory_records.db"
        self._init_sqlite()

    def _init_sqlite(self):
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS case_memory (
                id TEXT PRIMARY KEY,
                waste_class TEXT,
                strategy TEXT,
                outcome TEXT,
                embedding_json TEXT
            )
        """)
        conn.commit()
        conn.close()
        logger.info("sqlite_memory_initialized", path=self.sqlite_path)

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        dot_product = sum(x * y for x, y in zip(v1, v2))
        magnitude_1 = math.sqrt(sum(x * x for x in v1))
        magnitude_2 = math.sqrt(sum(x * x for x in v2))
        if not magnitude_1 or not magnitude_2:
            return 0.0
        return dot_product / (magnitude_1 * magnitude_2)

    def store_finding(
        self,
        record_id: str,
        waste_class: str,
        strategy: str,
        outcome: str,
        embedding: List[float],
    ):
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO case_memory (id, waste_class, strategy, outcome, embedding_json) VALUES (?, ?, ?, ?, ?)",
            (record_id, waste_class, strategy, outcome, json.dumps(embedding)),
        )
        conn.commit()
        conn.close()
        logger.info("memory_finding_stored", record_id=record_id, outcome=outcome)

    def query_semantic_similarity(
        self, query_vector: List[float], limit: int = 2
    ) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, waste_class, strategy, outcome, embedding_json FROM case_memory"
        )
        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            record_id, waste_class, strategy, outcome, embedding_json = row
            embedding = json.loads(embedding_json)
            score = self._cosine_similarity(query_vector, embedding)
            results.append({
                "id": record_id,
                "waste_class": waste_class,
                "strategy": strategy,
                "outcome": outcome,
                "similarity": score,
            })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]
