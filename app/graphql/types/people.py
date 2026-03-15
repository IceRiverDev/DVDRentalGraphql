from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Annotated, List, Optional

import strawberry
from strawberry.types import Info

if TYPE_CHECKING:
    from app.graphql.types.geography import AddressType
    from app.graphql.types.transactions import RentalType


@strawberry.type
class CustomerType:
    customer_id: int
    store_id: int
    first_name: str
    last_name: str
    email: Optional[str]
    address_id: int
    activebool: bool
    create_date: date
    last_update: Optional[datetime]
    active: Optional[int]

    @strawberry.field
    async def address(
        self, info: Info
    ) -> Optional[
        Annotated["AddressType", strawberry.lazy("app.graphql.types.geography")]
    ]:
        return await info.context.loaders.address.load(self.address_id)

    @strawberry.field
    async def rentals(
        self, info: Info
    ) -> List[
        Annotated["RentalType", strawberry.lazy("app.graphql.types.transactions")]
    ]:
        return await info.context.loaders.customer_rentals.load(self.customer_id)


@strawberry.type
class StaffType:
    staff_id: int
    first_name: str
    last_name: str
    address_id: int
    email: Optional[str]
    store_id: int
    active: bool
    username: str
    last_update: datetime


@strawberry.type
class StoreType:
    store_id: int
    manager_staff_id: int
    address_id: int
    last_update: datetime
