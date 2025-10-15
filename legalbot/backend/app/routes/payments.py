# backend/app/routes/payments.py
from fastapi import APIRouter, HTTPException, Query
from ..utils import create_razorpay_order

router = APIRouter(tags=["Payments"])

@router.post("/create-order")
async def create_order(
    amount_in_rupees: float = Query(..., description="Amount in INR"),
    receipt: str = Query(..., description="Unique receipt ID")
):
    """Create a Razorpay order."""
    try:
        order = create_razorpay_order(amount_in_rupees, receipt)
        if not order:
            raise HTTPException(status_code=500, detail="Failed to create Razorpay order.")
        return {"status": "success", "order": order}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment error: {str(e)}")
