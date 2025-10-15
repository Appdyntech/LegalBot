# backend/app/routes/documents.py
from fastapi import APIRouter, HTTPException
import httpx

router = APIRouter(tags=["Documents"])

MICROSERVICE_URL = "http://127.0.0.1:8002"

@router.get("/")
async def list_documents():
    """Fetch document list from external document microservice."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(f"{MICROSERVICE_URL}/api/v1/documents")
            if res.status_code != 200:
                raise HTTPException(status_code=res.status_code, detail="Failed to fetch documents.")
            return {"status": "success", "data": res.json()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching documents: {str(e)}")


@router.get("/{doc_id}")
async def get_document(doc_id: str):
    """Fetch single document details by ID from microservice."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(f"{MICROSERVICE_URL}/api/v1/documents/{doc_id}")
            if res.status_code != 200:
                raise HTTPException(status_code=res.status_code, detail="Document not found.")
            return {"status": "success", "document": res.json()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving document: {str(e)}")
