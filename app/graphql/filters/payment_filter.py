from __future__ import annotations

import enum
from typing import List, Optional

import strawberry

from app.graphql.filters.shared import (
    DateTimeFilter,
    FloatFilter,
    IntFilter,
    SortDirection,
)
from app.graphql.types.common import PageInfo
from app.graphql.types.transactions import PaymentType


@strawberry.enum
class PaymentSortField(enum.Enum):
    PAYMENT_DATE = "payment_date"
    AMOUNT = "amount"
    PAYMENT_ID = "payment_id"
    CUSTOMER_ID = "customer_id"


@strawberry.input
class PaymentFilter:
    payment_id: Optional[IntFilter] = None
    customer_id: Optional[IntFilter] = None
    staff_id: Optional[IntFilter] = None
    rental_id: Optional[IntFilter] = None
    amount: Optional[FloatFilter] = None
    payment_date: Optional[DateTimeFilter] = None


@strawberry.input
class PaymentSort:
    field: PaymentSortField = PaymentSortField.PAYMENT_DATE
    direction: SortDirection = SortDirection.DESC


@strawberry.type
class PaymentConnection:
    items: List[PaymentType]
    page_info: PageInfo
