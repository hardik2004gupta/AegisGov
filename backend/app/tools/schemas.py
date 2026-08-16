"""
Pydantic Tool Input Schemas — CLAUDE.md §10

Strict input contracts for all five governed tools.
Validation runs BEFORE OPA authorization and BEFORE handler execution.
Malformed parameters from agent-generated arguments must never reach handlers.

INVARIANT 6 (CLAUDE.md §26): Invalid parameters → NO handler execution.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, PositiveInt


class GetOrderSchema(BaseModel):
    order_id: PositiveInt


class GetCustomerSchema(BaseModel):
    customer_id: PositiveInt


class GetPaymentSchema(BaseModel):
    order_id: PositiveInt


class IssueRefundSchema(BaseModel):
    order_id: PositiveInt
    amount: float = Field(gt=0, le=5000)
    reason: str = Field(min_length=5, max_length=255)


class DeleteCustomerSchema(BaseModel):
    customer_id: PositiveInt
    reason: str = Field(default="Administrative deletion", min_length=5, max_length=255)
