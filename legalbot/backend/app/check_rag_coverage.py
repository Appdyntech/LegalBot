import psycopg2
from psycopg2.extras import RealDictCursor
from .config import get_settings
from .db_postgres import get_rag_conn

def check_rag_coverage(term: str, top_n: int = 5):
    """Check how many chunks match a term across retrieval modes."""
    conn = get_rag_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    table = "legal_document_chunks"

    print(f"\n🔍 Checking RAG coverage for term: '{term}'")

    # 1️⃣ Full-text Search
    cur.execute(f"""
        SELECT COUNT(*) AS matches FROM {table}
        WHERE to_tsvector('english', text) @@ plainto_tsquery('english', %s);
    """, (term,))
    fts_count = cur.fetchone()["matches"]

    # 2️⃣ ILIKE
    cur.execute(f"""
        SELECT COUNT(*) AS matches FROM {table}
        WHERE text ILIKE %s;
    """, (f"%{term}%",))
    ilike_count = cur.fetchone()["matches"]

    # 3️⃣ Metadata or Label
    cur.execute(f"""
        SELECT COUNT(*) AS matches FROM {table}
        WHERE predicted_label ILIKE %s OR metadata::text ILIKE %s;
    """, (f"%{term}%", f"%{term}%"))
    meta_count = cur.fetchone()["matches"]

    print(f"📘 Full-text matches: {fts_count}")
    print(f"📗 ILIKE matches: {ilike_count}")
    print(f"📙 Metadata matches: {meta_count}")

    # 4️⃣ Preview some examples
    cur.execute(f"""
        SELECT doc_id, chunk_id, LEFT(text, 200) AS preview
        FROM {table}
        WHERE text ILIKE %s
        LIMIT %s;
    """, (f"%{term}%", top_n))
    rows = cur.fetchall()

    if rows:
        print("\n📄 Example Chunks:")
        for r in rows:
            print(f"  - {r['doc_id']}:{r['chunk_id']} → {r['preview'][:150]}...")
    else:
        print("\n⚠️ No matching text chunks found.")

    cur.close()
    conn.close()

if __name__ == "__main__":
    for test_term in ["defamation", "bail", "contract", "tax", "negligence"]:
        check_rag_coverage(test_term)
