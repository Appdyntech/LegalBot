import logging
import re
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher
from .config import get_settings

settings = get_settings()

# --- Domain-specific keywords ---
DOMAIN_KEYWORDS = {
    "digitized_docs": ["resolution", "tax", "property", "contract", "clause", "section", "act", "ordinance"],
    "legal_chunks": ["tax", "property", "contract", "criminal", "family", "precedent", "appeal", "petition", "judgment"],
    "default": ["law", "justice", "case", "crime", "petition", "court", "rights", "complaint"]
}

# --- Classification hints ---
DOMAIN_TOPICS = {
    "criminal": ["threat", "murder", "assault", "violence", "harassment", "FIR", "police", "crime"],
    "civil": ["contract", "property", "agreement", "possession", "tenant", "tax", "building", "ownership"],
    "family": ["divorce", "maintenance", "child", "custody", "marriage", "dowry"],
    "corporate": ["company", "business", "share", "director", "audit", "resolution", "meeting"]
}

# --- Helper Functions ---
def get_query_intent(query: str) -> str:
    """Detects broad domain intent from the query."""
    q = query.lower()
    for domain, kws in DOMAIN_TOPICS.items():
        for kw in kws:
            if kw in q:
                return domain
    return "general"


def is_context_relevant(query: str, context: str, min_ratio: float = 0.35) -> bool:
    """Checks whether the context text is relevant to the query."""
    if not context or not query:
        return False
    ratio = SequenceMatcher(None, query.lower(), context.lower()).ratio()
    if ratio >= min_ratio:
        return True
    # fallback heuristic: keyword overlap
    query_tokens = set(re.findall(r'\b\w+\b', query.lower()))
    context_tokens = set(re.findall(r'\b\w+\b', context.lower()))
    overlap = len(query_tokens & context_tokens) / (len(query_tokens) + 1e-5)
    return overlap > 0.15


class RAGRetriever:
    """Retrieves context from MongoDB or PostgreSQL for RAG-based answering."""

    def __init__(self, mongo_client=None, postgres_conn=None, kb_label="legal_chunks", kb_backend="postgres", kb_info=None, config=None):
        self.mongo_client = mongo_client
        self.postgres_conn = postgres_conn
        self.kb_label = kb_label or "default"
        self.kb_backend = kb_backend
        self.kb_info = kb_info or {}
        self.config = config or {}

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not query.strip():
            return []

        logging.info(f"[RAGRetriever] 🔍 Query received: {query}")

        try:
            if self.kb_backend == "mongo":
                results = self._retrieve_mongo(query, top_k)
            elif self.kb_backend == "postgres":
                results = self._retrieve_postgres(query, top_k)
            else:
                results = []

            # --- Apply relevance filtering ---
            filtered = []
            intent = get_query_intent(query)
            for r in results:
                txt = r.get("text", "")
                if is_context_relevant(query, txt):
                    # Filter out unrelated domain (like tax for criminal)
                    if intent == "criminal" and "tax" in txt.lower():
                        continue
                    filtered.append(r)

            if not filtered:
                logging.warning(f"[RAGRetriever] ⚠️ No relevant context found; applying keyword fallback.")
                return self._keyword_fallback(query, top_k)

            logging.info(f"[RAGRetriever] ✅ Retrieved {len(filtered)} relevant chunks for intent={intent}")
            return filtered[:top_k]

        except Exception:
            logging.exception("RAGRetriever.retrieve failed")
            return []

    # ----------------- Unified Keyword Fallback -----------------
    def _keyword_fallback(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        kws = DOMAIN_KEYWORDS.get(self.kb_label, DOMAIN_KEYWORDS["default"])
        matched = []
        for kw in kws:
            if kw in query.lower():
                matched.append({
                    "text": f"User asked about '{kw}', but relevant context was not found. Please answer directly using general legal reasoning.",
                    "predicted_label": "general",
                    "source": "keyword_fallback",
                    "retrieval_mode": "keyword_fallback"
                })
        if not matched:
            matched = [{
                "text": f"No exact legal context found for: {query}. Please answer briefly and accurately.",
                "predicted_label": "general",
                "source": "keyword_fallback",
                "retrieval_mode": "keyword_fallback"
            }]
        return matched[:top_k]

    # ----------------- Mongo Retrieval -----------------
    def _retrieve_mongo(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if self.mongo_client is None:
            return []
        db_name = self.kb_info.get("db") or settings.MONGO_DB
        coll_name = self.kb_info.get("collection") or settings.MONGO_COLLECTION
        db = self.mongo_client[db_name]
        coll = db[coll_name]

        try:
            conds = {"$or": [{f: {"$regex": re.escape(query), "$options": "i"}} for f in ["content", "text", "body"]]}
            cursor = coll.find(conds, projection={"_id": 0, "content": 1, "metadata": 1}).limit(top_k)
            out = []
            for d in cursor:
                txt = d.get("content") or ""
                out.append({
                    "text": txt,
                    "predicted_label": d.get("metadata", {}).get("predicted_label"),
                    "source": f"mongo:{db_name}/{coll_name}",
                    "metadata": d.get("metadata", {}),
                    "retrieval_mode": "mongo:exact"
                })
            if out:
                return out
        except Exception:
            logging.exception("mongo search failed")

        return []

    # ----------------- Postgres Retrieval -----------------
    def _retrieve_postgres(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if self.postgres_conn is None:
            return []

        table = self.kb_info.get("table") or "legal_document_chunks"
        try:
            cur = self.postgres_conn.cursor()
            sql = f"""
                SELECT doc_id, chunk_id, text, predicted_label, metadata
                FROM {table}
                WHERE text ILIKE %s
                LIMIT %s;
            """
            cur.execute(sql, (f"%{query}%", top_k))
            rows = cur.fetchall()
            cur.close()

            out = []
            for r in rows:
                doc_id, chunk_id, content, label, meta = r
                out.append({
                    "text": content,
                    "predicted_label": label.strip().lower() if label else None,
                    "source": f"postgres:{table}:{doc_id}:{chunk_id}",
                    "metadata": meta or {},
                    "retrieval_mode": "postgres:ilike"
                })
            return out
        except Exception:
            logging.exception("postgres search failed")
            return []
