"""
Payment CRUD Router
===================
POST   /api/payments/           → Create payment
GET    /api/payments/           → List payments (filter by status, customer_id)
GET    /api/payments/{id}       → Get one payment
PUT    /api/payments/{id}       → Update payment
DELETE /api/payments/{id}       → Delete payment
POST   /api/payments/{id}/refund → Refund payment
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from database import (
    db_create_payment, db_list_payments, db_get_payment,
    db_update_payment, db_delete_payment
)

router = APIRouter()

# ── Pydantic Models ───────────────────────────────────────────────────────────
class PaymentCreate(BaseModel):
    amount:      float       = Field(..., gt=0, description="Amount > 0")
    currency:    str         = Field("USD", max_length=5)
    customer_id: str         = Field(..., min_length=1)
    description: Optional[str] = ""

    class Config:
        json_schema_extra = {"example": {
            "amount": 250.00, "currency": "USD",
            "customer_id": "CUST-001", "description": "Order #1042 payment"
        }}

class PaymentUpdate(BaseModel):
    amount:      Optional[float] = Field(None, gt=0)
    currency:    Optional[str]   = None
    description: Optional[str]  = None
    status:      Optional[str]  = Field(None, pattern="^(pending|completed|failed|refunded)$")

    class Config:
        json_schema_extra = {"example": {"status": "completed", "amount": 300.00}}

# ── CREATE ────────────────────────────────────────────────────────────────────
@router.post("/", status_code=201)
def create_payment(data: PaymentCreate):
    """Create a new payment record."""
    payment = db_create_payment(data.dict())
    return {
        "message": "✅ Payment created successfully",
        "payment": payment
    }

# ── LIST ──────────────────────────────────────────────────────────────────────
@router.get("/")
def list_payments(
    status:      Optional[str] = Query(None, description="Filter by status"),
    customer_id: Optional[str] = Query(None, description="Filter by customer"),
):
    """List all payments with optional filters."""
    payments = db_list_payments(status=status, customer_id=customer_id)
    return {
        "total":    len(payments),
        "payments": payments
    }

# ── GET ONE ───────────────────────────────────────────────────────────────────
@router.get("/{payment_id}")
def get_payment(payment_id: int):
    """Get a single payment by ID."""
    p = db_get_payment(payment_id)
    if not p:
        raise HTTPException(404, f"Payment {payment_id} not found")
    return p

# ── UPDATE ────────────────────────────────────────────────────────────────────
@router.put("/{payment_id}")
def update_payment(payment_id: int, data: PaymentUpdate):
    """Update payment fields."""
    p = db_update_payment(payment_id, data.dict(exclude_none=True))
    if not p:
        raise HTTPException(404, f"Payment {payment_id} not found")
    return {"message": "✅ Payment updated", "payment": p}

# ── DELETE ────────────────────────────────────────────────────────────────────
@router.delete("/{payment_id}")
def delete_payment(payment_id: int):
    """Delete a payment record."""
    if not db_delete_payment(payment_id):
        raise HTTPException(404, f"Payment {payment_id} not found")
    return {"message": f"✅ Payment {payment_id} deleted"}

# ── REFUND ────────────────────────────────────────────────────────────────────
@router.post("/{payment_id}/refund")
def refund_payment(payment_id: int):
    """Refund a completed payment."""
    p = db_get_payment(payment_id)
    if not p:
        raise HTTPException(404, f"Payment {payment_id} not found")
    if p["status"] != "completed":
        raise HTTPException(400, f"Only completed payments can be refunded. Current status: {p['status']}")
    updated = db_update_payment(payment_id, {"status": "refunded"})
    return {"message": "✅ Payment refunded", "payment": updated}
