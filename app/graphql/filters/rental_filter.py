from __future__ import annotations

import enum
from typing import Annotated, List, Optional

import strawberry

from app.graphql.filters.shared import DateTimeFilter, IntFilter, SortDirection
from app.graphql.types.common import PageInfo


@strawberry.enum
class RentalSortField(enum.Enum):
    RENTAL_DATE = "rental_date"
    RETURN_DATE = "return_date"
    RENTAL_ID = "rental_id"
    CUSTOMER_ID = "customer_id"


@strawberry.input
class RentalFilter:
    rental_id: Optional[IntFilter] = None
    rental_date: Optional[DateTimeFilter] = None
    customer_id: Optional[IntFilter] = None
    staff_id: Optional[IntFilter] = None
    inventory_id: Optional[IntFilter] = None
    film_id: Optional[IntFilter] = None
    is_returned: Optional[bool] = None
    is_overdue: Optional[bool] = None


@strawberry.input
class RentalSort:
    field: RentalSortField = RentalSortField.RENTAL_DATE
    direction: SortDirection = SortDirection.DESC


@strawberry.type
class RentalConnection:
    items: List[Annotated["RentalType", strawberry.lazy("app.graphql.types.transactions")]]
    page_info: PageInfo
