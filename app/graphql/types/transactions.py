from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Annotated, List, Optional

import strawberry
from strawberry.types import Info

if TYPE_CHECKING:
    from app.graphql.types.film import FilmType
    from app.graphql.types.people import CustomerType


@strawberry.type
class InventoryType:
    inventory_id: int
    film_id: int
    store_id: int
    last_update: datetime

    @strawberry.field
    async def film(
        self, info: Info
    ) -> Optional[Annotated["FilmType", strawberry.lazy("app.graphql.types.film")]]:
        return await info.context.loaders.film.load(self.film_id)


@strawberry.type
class RentalType:
    rental_id: int
    rental_date: datetime
    inventory_id: int
    customer_id: int
    return_date: Optional[datetime]
    staff_id: int
    last_update: datetime

    @strawberry.field
    async def inventory(
        self, info: Info
    ) -> Optional[Annotated["InventoryType", strawberry.lazy("app.graphql.types.transactions")]]:
        return await info.context.loaders.inventory.load(self.inventory_id)

    @strawberry.field
    async def customer(
        self, info: Info
    ) -> Optional[Annotated["CustomerType", strawberry.lazy("app.graphql.types.people")]]:
        return await info.context.loaders.customer.load(self.customer_id)

    @strawberry.field
    async def payments(
        self, info: Info
    ) -> List[Annotated["PaymentType", strawberry.lazy("app.graphql.types.transactions")]]:
        return await info.context.loaders.rental_payments.load(self.rental_id)


@strawberry.type
class PaymentType:
    payment_id: int
    customer_id: int
    staff_id: int
    rental_id: int
    amount: Decimal
    payment_date: datetime


@strawberry.type
class PaymentSummaryType:
    total_count: int
    total_amount: Decimal
    average_amount: Decimal
    min_amount: Decimal
    max_amount: Decimal
