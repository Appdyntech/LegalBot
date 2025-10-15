import os
import pandas as pd
from sqlalchemy import create_engine

# Database config
DB_USER = "postgres"
DB_PASS = "Google%40123"  # update with actual password
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "legal_chunks_db"
TABLE = "legal_document_chunks"

# Path to parquet directory
PARQUET_DIR = r"C:\Users\joyb1\Downloads\mcci_chunks\mcci_chunks"

# Create engine
engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Scan parquet files
parquet_files = sorted(
    [os.path.join(PARQUET_DIR, f) for f in os.listdir(PARQUET_DIR) if f.endswith(".parquet")]
)
print(f"Found {len(parquet_files)} parquet files.")

for parquet_file in parquet_files:
    print(f"Ingesting {parquet_file} ...")
    df = pd.read_parquet(parquet_file)

    # Drop conflicting id column if exists
    if "id" in df.columns:
        df = df.drop(columns=["id"])

    # Force assign doc_id = filename
    base_name = os.path.basename(parquet_file).replace(".parquet", "")
    df["doc_id"] = base_name

    # Force assign chunk_id = row index starting from 1
    df["chunk_id"] = df.index + 1

    # Ensure metadata exists
    if "metadata" not in df.columns:
        df["metadata"] = None

    # Convert embeddings if stored as string
    if "embedding" in df.columns and df["embedding"].dtype == object:
        df["embedding"] = df["embedding"].apply(
            lambda x: x if isinstance(x, (dict, list)) else None
        )

    # Keep only the expected columns
    valid_cols = ["doc_id", "chunk_id", "text", "predicted_label", "embedding", "metadata"]
    df = df[[c for c in valid_cols if c in df.columns]]

    # Insert into DB
    df.to_sql(TABLE, engine, if_exists="append", index=False, method="multi", chunksize=500)
    print(f"Inserted {len(df)} rows from {parquet_file}.")
