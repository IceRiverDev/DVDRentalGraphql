from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Annotated, List, Optional

import strawberry
from sqlalchemy import select
from strawberry.types import Info

from app.graphql.filters.payment_filter import PaymentFilter
from app.graphql.filters.rental_filter import RentalFilter
from app.graphql.filters.shared import apply_datetime_filter, apply_float_filter, apply_int_filter

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

    @strawberry.field
    async def rentals(
        self,
        info: Info,
        filter: Optional[RentalFilter] = None,
    ) -> List[Annotated["RentalType", strawberry.lazy("app.graphql.types.transactions")]]:
        if filter is None:
            return await info.context.loaders.inventory_rentals.load(self.inventory_id)
        from app.graphql.dataloaders import _rental_to_type
        from app.models.models import Rental

        async with info.context.session_factory() as db:
            q = select(Rental).where(Rental.inventory_id == self.inventory_id)
            q = apply_int_filter(q, Rental.rental_id, filter.rental_id)
            q = apply_int_filter(q, Rental.customer_id, filter.customer_id)
            q = apply_datetime_filter(q, Rental.rental_date, filter.rental_date)
            if filter.is_returned is True:
                q = q.where(Rental.return_date.is_not(None))
            elif filter.is_returned is False:
                q = q.where(Rental.return_date.is_(None))
            result = await db.execute(q)
            return [_rental_to_type(r) for r in result.scalars().all()]


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
    ) -> Optional[
        Annotated["InventoryType", strawberry.lazy("app.graphql.types.transactions")]
    ]:
        return await info.context.loaders.inventory.load(self.inventory_id)

    @strawberry.field
    async def customer(
        self, info: Info
    ) -> Optional[
        Annotated["CustomerType", strawberry.lazy("app.graphql.types.people")]
    ]:
        return await info.context.loaders.customer.load(self.customer_id)

    @strawberry.field
    async def payments(
        self,
        info: Info,
        filter: Optional[PaymentFilter] = None,
    ) -> List[
        Annotated["PaymentType", strawberry.lazy("app.graphql.types.transactions")]
    ]:
        if filter is None:
            return await info.context.loaders.rental_payments.load(self.rental_id)
        from app.graphql.dataloaders import _payment_to_type
        from app.models.models import Payment

        async with info.context.session_factory() as db:
            q = select(Payment).where(Payment.rental_id == self.rental_id)
            q = apply_int_filter(q, Payment.payment_id, filter.payment_id)
            q = apply_float_filter(q, Payment.amount, filter.amount)
            q = apply_datetime_filter(q, Payment.payment_date, filter.payment_date)
            result = await db.execute(q)
            return [_payment_to_type(p) for p in result.scalars().all()]


@strawberry.type
class PaymentType:
    payment_id: int
    customer_id: int
    staff_id: int
    rental_id: int
    amount: Decimal
    payment_date: datetime

    @strawberry.field
    async def customer(
        self, info: Info
    ) -> Optional[
        Annotated["CustomerType", strawberry.lazy("app.graphql.types.people")]
    ]:
        return await info.context.loaders.customer.load(self.customer_id)

    @strawberry.field
    async def rental(
        self, info: Info
    ) -> Optional[
        Annotated["RentalType", strawberry.lazy("app.graphql.types.transactions")]
    ]:
        return await info.context.loaders.rental.load(self.rental_id)


@strawberry.type
class PaymentSummaryType:
    total_count: int
    total_amount: Decimal
    average_amount: Decimal
    min_amount: Decimal
    max_amount: Decimal
