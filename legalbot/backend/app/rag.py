import logging
import re
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher
import psycopg2
from psycopg2.extras import RealDictCursor
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import RegexpTokenizer
from fuzzywuzzy import fuzz
from collections import defaultdict

from .config import get_settings
from .db_postgres import get_rag_conn

settings = get_settings()

# ============================================================
# DOMAIN CONFIGURATION
# ============================================================

DOMAIN_KEYWORDS = {
    "digitized_docs": ["resolution", "tax", "property", "contract", "clause", "section", "act", "ordinance"],
    "legal_chunks": ["tax", "property", "contract", "criminal", "family", "precedent", "appeal", "petition", "judgment"],
    "default": ["law", "justice", "case", "crime", "petition", "court", "rights", "complaint"],
}

DOMAIN_TOPICS = {
    "criminal": ["threat", "murder", "assault", "violence", "harassment", "fir", "police", "crime", "bail"],
    "civil": ["contract", "property", "agreement", "possession", "tenant", "tax", "building", "ownership"],
    "family": ["divorce", "maintenance", "child", "custody", "marriage", "dowry"],
    "corporate": ["company", "business", "share", "director", "audit", "resolution", "meeting"],
}

# ============================================================
# DYNAMIC ALIAS SYSTEM
# ============================================================

DYNAMIC_ALIAS_MAP = defaultdict(set)


def normalize_name(text: str) -> str:
    """Normalize text for alias comparison."""
    return re.sub(r"[^a-z0-9 ]+", "", text.strip().lower())


def build_dynamic_aliases(chunks, threshold: int = 85):
    """
    Build alias relationships dynamically from all proper names in legal text chunks.
    Creates pairs of highly similar names (Mukhtar ↔ Mukhtiar, Brijender ↔ Brijendra).
    """
    global DYNAMIC_ALIAS_MAP
    names = set()

    for c in chunks:
        txt = c.get("text", "")
        # Capture name-like phrases: "Mukhtar Singh", "Brijendra Meena", etc.
        for token in re.findall(r"\b[A-Z][a-z]{2,}\s[A-Z][a-z]{2,}\b", txt):
            names.add(normalize_name(token))

    name_list = list(names)
    logging.info(f"[AliasBuilder] Found {len(name_list)} potential name tokens.")

    for i, n1 in enumerate(name_list):
        for n2 in name_list[i + 1:]:
            score = fuzz.ratio(n1, n2)
            if score >= threshold and n1 != n2:
                DYNAMIC_ALIAS_MAP[n1].add(n2)
                DYNAMIC_ALIAS_MAP[n2].add(n1)

    logging.info(f"[AliasBuilder] ✅ Built {len(DYNAMIC_ALIAS_MAP)} alias groups.")
    return DYNAMIC_ALIAS_MAP


def expand_query_with_aliases(query: str) -> str:
    """
    Expand query dynamically using alias map.
    Example: 'mukhtar singh' -> 'mukhtar singh mukhtiar singh'
    """
    q_norm = normalize_name(query)
    expanded = set(q_norm.split())

    for name, aliases in DYNAMIC_ALIAS_MAP.items():
        if name in q_norm:
            expanded |= aliases

    if len(expanded) > len(q_norm.split()):
        logging.info(f"[AliasExpansion] Expanded query -> {' '.join(expanded)}")

    return " ".join(expanded)


# ============================================================
# HELPERS
# ============================================================

def get_query_intent(query: str) -> str:
    """Detects broad legal domain (criminal, civil, etc.) from query."""
    q = query.lower()
    for domain, kws in DOMAIN_TOPICS.items():
        if any(kw in q for kw in kws):
            return domain
    return "general"


def is_context_relevant(query: str, context: str, min_ratio: float = 0.35) -> bool:
    """Checks semantic + token overlap relevance between query and text."""
    if not context or not query:
        return False
    ratio = SequenceMatcher(None, query.lower(), context.lower()).ratio()
    if ratio >= min_ratio:
        return True
    q_tokens = set(re.findall(r"\b\w+\b", query.lower()))
    c_tokens = set(re.findall(r"\b\w+\b", context.lower()))
    overlap = len(q_tokens & c_tokens) / (len(q_tokens) + 1e-5)
    return overlap > 0.15


# ============================================================
# RAG RETRIEVER
# ============================================================

class RAGRetriever:
    """Hybrid PostgreSQL-based retriever with ranked search and adaptive fuzzy fallback."""

    def __init__(self, postgres_conn=None, kb_label="legal_chunks", kb_info=None, config=None):
        self.postgres_conn = postgres_conn
        self.kb_label = kb_label
        self.kb_info = kb_info or {}
        self.config = config or {}

        # Build alias map dynamically (once per app start)
        try:
            if not DYNAMIC_ALIAS_MAP:
                logging.info("[RAGRetriever] 🔧 Building dynamic alias map...")
                temp_conn = get_rag_conn()  # ✅ Use a separate connection
                if temp_conn:
                    with temp_conn.cursor(cursor_factory=RealDictCursor) as cur:
                        table = self.kb_info.get("table", "legal_document_chunks")
                        cur.execute(f"SELECT text FROM {table} LIMIT 5000;")
                        chunks = cur.fetchall()
                        build_dynamic_aliases(chunks)
                    temp_conn.close()  # ✅ Safe to close here
        except Exception as e:
            logging.warning(f"[RAGRetriever] ⚠️ Alias map build skipped: {e}")

    # --------------------------------------------------------
    # Public Retrieval
    # --------------------------------------------------------
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not query.strip():
            return []

        # 🧠 Expand with aliases
        query_expanded = expand_query_with_aliases(query)
        logging.info(f"[RAGRetriever] 🔍 Query: {query_expanded}")

        conn = self.postgres_conn or get_rag_conn()
        if not conn:
            logging.error("[RAGRetriever] ❌ No Postgres connection available.")
            return self._keyword_fallback(query_expanded, top_k)

        try:
            results = self._retrieve_postgres(conn, query_expanded, top_k)
            intent = get_query_intent(query_expanded)

            filtered = [
                r for r in results
                if is_context_relevant(query_expanded, r.get("text", "")) and not (
                    intent == "criminal" and "tax" in (r.get("text") or "").lower()
                )
            ]

            if filtered:
                logging.info(f"[RAGRetriever] ✅ Retrieved {len(filtered)} relevant chunks for intent='{intent}'")
                return filtered[:top_k]

            logging.warning("[RAGRetriever] ⚠️ No relevant matches — activating adaptive fuzzy fallback.")
            return self._adaptive_fuzzy_fallback(conn, query_expanded, top_k)

        except Exception as e:
            logging.exception(f"[RAGRetriever] ❌ Retrieval error: {e}")
            return self._adaptive_fuzzy_fallback(conn, query_expanded, top_k)
        finally:
            try:
                conn.close()
            except Exception:
                pass

    # --------------------------------------------------------
    # PostgreSQL Retrieval Logic
    # --------------------------------------------------------
    def _retrieve_postgres(self, conn, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Ranked retrieval using FTS, ILIKE, and metadata."""
        table = self.kb_info.get("table") or "legal_document_chunks"
        cur = conn.cursor()
        rows, retrieval_mode = [], "none"

        try:
            sql_fts = f"""
                SELECT id, doc_id, chunk_id, text, predicted_label, metadata,
                       ts_rank_cd(to_tsvector('english', text), plainto_tsquery('english', %s)) AS rank
                FROM {table}
                WHERE to_tsvector('english', text) @@ plainto_tsquery('english', %s)
                ORDER BY rank DESC
                LIMIT %s;
            """
            cur.execute(sql_fts, (query, query, top_k * 3))
            rows = cur.fetchall()
            retrieval_mode = "postgres:fts"

            if not rows:
                sql_ilike = f"""
                    SELECT id, doc_id, chunk_id, text, predicted_label, metadata
                    FROM {table}
                    WHERE text ILIKE %s
                    LIMIT %s;
                """
                cur.execute(sql_ilike, (f"%{query}%", top_k * 3))
                rows = cur.fetchall()
                retrieval_mode = "postgres:ilike"

            if not rows:
                sql_meta = f"""
                    SELECT id, doc_id, chunk_id, text, predicted_label, metadata
                    FROM {table}
                    WHERE predicted_label ILIKE %s OR metadata::text ILIKE %s
                    LIMIT %s;
                """
                cur.execute(sql_meta, (f"%{query}%", f"%{query}%", top_k * 3))
                rows = cur.fetchall()
                retrieval_mode = "postgres:label_meta"

            results = []
            for r in rows:
                id_, doc_id, chunk_id, text, label, meta, *rest = r + (None,) * (7 - len(r))
                score = rest[0] if rest else 0.0
                results.append({
                    "id": id_,
                    "text": text,
                    "predicted_label": (label or "").strip().lower() if label else None,
                    "metadata": meta or {},
                    "source": f"{table}:{doc_id}:{chunk_id}",
                    "score": float(score) if score else 0.0,
                    "retrieval_mode": retrieval_mode,
                })

            logging.info(f"[RAGRetriever] ✅ Retrieved {len(results)} rows via {retrieval_mode}")
            return sorted(results, key=lambda x: x["score"], reverse=True)

        except Exception:
            logging.exception("[RAGRetriever] ❌ Postgres RAG retrieval failed.")
            return []
        finally:
            cur.close()

    # --------------------------------------------------------
    # 🧩 Adaptive Fuzzy Fallback
    # --------------------------------------------------------
    def _adaptive_fuzzy_fallback(self, conn, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        logging.info("[RAGRetriever] 🔁 Adaptive fuzzy fallback initiated")

        lemmatizer = WordNetLemmatizer()
        tokenizer = RegexpTokenizer(r"\b\w+\b")
        query_lower = query.lower()
        query_tokens = [lemmatizer.lemmatize(w) for w in tokenizer.tokenize(query_lower)]

        name_phrases = re.findall(r"\b[a-z]{3,}\s[a-z]{3,}\b", query_lower)
        name_phrases += re.findall(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+", query)
        name_phrases = list(set([p.lower() for p in name_phrases]))

        name_tokens = [w for ph in name_phrases for w in ph.split()]
        name_tokens = list(set(name_tokens))

        intent = get_query_intent(query_lower)
        domain_kws = DOMAIN_TOPICS.get(intent, []) + DOMAIN_KEYWORDS.get(self.kb_label, [])
        query_tokens.extend(domain_kws)

        fuzzy_weight = 6 if len(query_tokens) < 10 else 4

        matches = []
        table = self.kb_info.get("table") or "legal_document_chunks"

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"SELECT doc_id, chunk_id, text, metadata FROM {table} LIMIT 20000;")
                rows = cur.fetchall()

            for r in rows:
                text = (r["text"] or "").lower()
                text = re.sub(r'[^a-z0-9\s]', ' ', text)

                token_overlap = sum(1 for tok in query_tokens if tok in text)
                fuzzy = SequenceMatcher(None, query_lower, text[:800]).ratio()
                score = token_overlap + fuzzy * fuzzy_weight

                for ph in name_phrases:
                    words = ph.split()
                    hits = sum(1 for w in words if w in text)
                    if hits == len(words):
                        score += 3.0
                    elif hits >= 1:
                        score += 1.8

                if len([n for n in name_tokens if n in text]) >= 2:
                    score += 1.5

                if settings.DEBUG_RAG:
                    matched_tokens = [tok for tok in query_tokens if tok in text]
                    matched_phrases = [ph for ph in name_phrases if ph in text]
                    logging.info(
                        f"[DEBUG_RAG] text[:80]={text[:80]!r} | score={round(score,3)} | "
                        f"tokens={matched_tokens} | phrases={matched_phrases} | fuzzy={round(fuzzy,3)}"
                    )

                if score > 3.0:
                    r["score"] = round(score, 3)
                    r["source"] = f"{table}:{r['doc_id']}:{r['chunk_id']}"
                    r["retrieval_mode"] = "adaptive_fuzzy_fallback"
                    matches.append(r)

            matches = sorted(matches, key=lambda x: x["score"], reverse=True)[:top_k]
            logging.info(f"[RAGRetriever] ✅ Adaptive fuzzy fallback matched {len(matches)} chunks")

            if matches:
                logging.info(f"[RAGRetriever] 🔍 Top fuzzy matches for '{query}':")
                for m in matches[:5]:
                    snippet = (m['text'] or '').replace('\n', ' ')[:140]
                    logging.info(f"   • {m['source']} | Score={m['score']}: {snippet}...")

            if not matches:
                return self._keyword_fallback(query, top_k)
            return matches

        except Exception as e:
            logging.error(f"[RAGRetriever] ❌ Adaptive fallback scan error: {e}")
            return self._keyword_fallback(query, top_k)

    # --------------------------------------------------------
    # Minimal Keyword Fallback
    # --------------------------------------------------------
    def _keyword_fallback(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        logging.warning(f"[RAGRetriever] ⚠️ Default keyword fallback for: {query}")
        kws = DOMAIN_KEYWORDS.get(self.kb_label, DOMAIN_KEYWORDS["default"])
        matched = [
            {
                "text": f"General legal context for '{kw}' — provide background explanation if relevant.",
                "predicted_label": "general",
                "source": "keyword_fallback",
                "retrieval_mode": "keyword_fallback",
                "score": 0.1,
            }
            for kw in kws if kw in query.lower()
        ]
        if not matched:
            matched = [{
                "text": f"No direct match for: {query}. Provide general legal reasoning.",
                "predicted_label": "general",
                "source": "keyword_fallback",
                "retrieval_mode": "keyword_fallback",
                "score": 0.0,
            }]
        return matched[:top_k]
