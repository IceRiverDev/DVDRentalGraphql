from __future__ import annotations

import enum
from typing import Annotated, List, Optional

import strawberry

from app.graphql.filters.shared import (
    DateFilter,
    IntFilter,
    SortDirection,
    StringFilter,
)
from app.graphql.types.common import PageInfo


@strawberry.enum
class CustomerSortField(enum.Enum):
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    CUSTOMER_ID = "customer_id"
    CREATE_DATE = "create_date"
    EMAIL = "email"


@strawberry.input
class CustomerFilter:
    customer_id: Optional[IntFilter] = None
    name: Optional[StringFilter] = None
    email: Optional[StringFilter] = None
    active: Optional[bool] = None
    store_id: Optional[IntFilter] = None
    create_date: Optional[DateFilter] = None


@strawberry.input
class CustomerSort:
    field: CustomerSortField = CustomerSortField.LAST_NAME
    direction: SortDirection = SortDirection.ASC


@strawberry.type
class CustomerConnection:
    items: List[Annotated["CustomerType", strawberry.lazy("app.graphql.types.people")]]
    page_info: PageInfo
