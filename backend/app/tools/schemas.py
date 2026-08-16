# Phase 3: Pydantic Tool Input Schemas
#
# Strict input contracts for all five governed tools.
# Validation runs BEFORE OPA authorization and BEFORE handler execution.
# Malformed parameters must never reach tool handlers (CLAUDE.md §10).
#
# Example contracts (CLAUDE.md §10):
#
# class GetOrderSchema(BaseModel):
#     order_id: PositiveInt
#
# class IssueRefundSchema(BaseModel):
#     order_id: PositiveInt
#     amount:   float = Field(gt=0, le=5000)
#     reason:   str   = Field(min_length=5, max_length=255)
#
# class DeleteCustomerSchema(BaseModel):
#     customer_id: PositiveInt

from __future__ import annotations

# TODO Phase 3: define all 5 Pydantic schemas
