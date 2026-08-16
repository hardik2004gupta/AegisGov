"""
Tool Handlers — Secure DB Operations

These are the ONLY functions that may execute database operations for
the five governed tools. They are called exclusively by the Secure Tool
Gateway after the full pipeline has passed:
    Registry → Pydantic → Runtime Safety → OPA → Risk → [HITL?] → EXECUTE

ARCHITECTURAL INVARIANT (CLAUDE.md §8, INVARIANT 1):
    Agents MUST NOT import or invoke these functions.
    Only gateway.py may call a handler — after all checks pass.

Each handler:
    - Accepts a dict of validated (Pydantic-checked) arguments
    - Accepts an AsyncSession already in a role-switched transaction
    - Returns a sanitized response dict (no SQLAlchemy objects, no raw rows)
    - Raises ValueError for business-logic failures (not-found, etc.)

Result sanitization (CLAUDE.md §27): handlers return clean dicts, never
    SQLAlchemy model objects, internal fields, or credentials.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Customer, Order, Payment

logger = logging.getLogger(__name__)


async def get_order_handler(args: dict, db: AsyncSession) -> dict:
    """Return safe order information. Uses order_reader role."""
    order_id: int = args["order_id"]
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if order is None:
        raise ValueError(f"Order {order_id} not found")

    return {
        "order_id": order.id,
        "status": order.status,
        "total_amount": float(order.total_amount),
        "currency": order.currency,
        "description": order.description,
        "customer_id": order.customer_id,
        "created_at": order.created_at.isoformat() if order.created_at else None,
    }


async def get_customer_handler(args: dict, db: AsyncSession) -> dict:
    """Return safe customer information. Uses order_reader role."""
    customer_id: int = args["customer_id"]
    result = await db.execute(
        select(Customer).where(Customer.id == customer_id)
    )
    customer = result.scalar_one_or_none()
    if customer is None:
        raise ValueError(f"Customer {customer_id} not found")

    return {
        "customer_id": customer.id,
        "full_name": customer.full_name,
        "email": customer.email,
        "created_at": customer.created_at.isoformat() if customer.created_at else None,
    }


async def get_payment_handler(args: dict, db: AsyncSession) -> dict:
    """Return safe payment information. Uses billing_reader role."""
    order_id: int = args["order_id"]

    # Verify order exists
    order_result = await db.execute(select(Order).where(Order.id == order_id))
    order = order_result.scalar_one_or_none()
    if order is None:
        raise ValueError(f"Order {order_id} not found")

    # Get payment(s) for this order
    payment_result = await db.execute(
        select(Payment).where(Payment.order_id == order_id)
    )
    payment = payment_result.scalar_one_or_none()
    if payment is None:
        raise ValueError(f"No payment found for order {order_id}")

    return {
        "payment_id": payment.id,
        "order_id": order_id,
        "amount": float(payment.amount),
        "currency": payment.currency,
        "status": payment.status,
        "payment_method": payment.payment_method,
        "refund_amount": float(payment.refund_amount) if payment.refund_amount else None,
        "refund_reason": payment.refund_reason,
    }


async def issue_refund_handler(args: dict, db: AsyncSession) -> dict:
    """Apply a refund to the payment for an order. Uses billing_writer role.

    Transactional: the role-switched session ensures atomicity.
    The gateway begins the transaction before calling this handler.
    """
    order_id: int = args["order_id"]
    amount: float = float(args["amount"])
    reason: str = args["reason"]

    # Verify order exists
    order_result = await db.execute(select(Order).where(Order.id == order_id))
    order = order_result.scalar_one_or_none()
    if order is None:
        raise ValueError(f"Order {order_id} not found")

    # Find the payment for this order
    payment_result = await db.execute(
        select(Payment).where(Payment.order_id == order_id)
    )
    payment = payment_result.scalar_one_or_none()
    if payment is None:
        raise ValueError(f"No payment found for order {order_id}")

    if payment.status == "REFUNDED":
        raise ValueError(f"Order {order_id} has already been refunded")

    # Apply the refund mutation (INVARIANT 8: only reached after full gateway pipeline)
    payment.status = "REFUNDED"
    payment.refund_amount = amount
    payment.refund_reason = reason
    payment.refunded_at = datetime.now(timezone.utc)
    db.add(payment)

    logger.info(
        "Refund applied order_id=%s amount=%.2f reason=%r",
        order_id, amount, reason,
    )

    return {
        "order_id": order_id,
        "payment_id": payment.id,
        "refund_amount": amount,
        "reason": reason,
        "status": "REFUNDED",
    }


async def delete_customer_handler(args: dict, db: AsyncSession) -> dict:
    """Permanently delete a customer and all related records. Uses admin_writer role.

    INVARIANT 5 (CLAUDE.md §26): This handler is ONLY reachable after:
        OPA ALLOW + CRITICAL risk + APPROVED HITL request.

    Delete order: payments → orders → customer (reverse FK dependency).
    """
    customer_id: int = args["customer_id"]

    result = await db.execute(
        select(Customer).where(Customer.id == customer_id)
    )
    customer = result.scalar_one_or_none()
    if customer is None:
        raise ValueError(f"Customer {customer_id} not found")

    customer_info = {
        "customer_id": customer.id,
        "full_name": customer.full_name,
        "email": customer.email,
    }

    # Cascade delete: remove payments → orders → customer
    await db.execute(
        delete(Payment).where(Payment.customer_id == customer_id)
    )
    await db.execute(
        delete(Order).where(Order.customer_id == customer_id)
    )
    await db.delete(customer)

    logger.warning(
        "Customer DELETED customer_id=%s email=%s",
        customer_id,
        customer_info["email"],
    )

    return {**customer_info, "status": "DELETED"}
