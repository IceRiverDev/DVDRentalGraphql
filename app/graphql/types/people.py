from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Annotated, List, Optional

import strawberry
from sqlalchemy import select
from strawberry.types import Info

from app.graphql.filters.payment_filter import PaymentFilter
from app.graphql.filters.rental_filter import RentalFilter
from app.graphql.filters.shared import apply_datetime_filter, apply_float_filter, apply_int_filter

if TYPE_CHECKING:
    from app.graphql.types.geography import AddressType
    from app.graphql.types.transactions import PaymentType, RentalType


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
        self,
        info: Info,
        filter: Optional[RentalFilter] = None,
    ) -> List[
        Annotated["RentalType", strawberry.lazy("app.graphql.types.transactions")]
    ]:
        if filter is None:
            return await info.context.loaders.customer_rentals.load(self.customer_id)
        from app.graphql.dataloaders import _rental_to_type
        from app.models.models import Rental

        async with info.context.session_factory() as db:
            q = select(Rental).where(Rental.customer_id == self.customer_id)
            q = apply_int_filter(q, Rental.rental_id, filter.rental_id)
            q = apply_datetime_filter(q, Rental.rental_date, filter.rental_date)
            q = apply_int_filter(q, Rental.inventory_id, filter.inventory_id)
            if filter.is_returned is True:
                q = q.where(Rental.return_date.is_not(None))
            elif filter.is_returned is False:
                q = q.where(Rental.return_date.is_(None))
            result = await db.execute(q)
            return [_rental_to_type(r) for r in result.scalars().all()]

    @strawberry.field
    async def payments(
        self,
        info: Info,
        filter: Optional[PaymentFilter] = None,
    ) -> List[
        Annotated["PaymentType", strawberry.lazy("app.graphql.types.transactions")]
    ]:
        if filter is None:
            return await info.context.loaders.customer_payments.load(self.customer_id)
        from app.graphql.dataloaders import _payment_to_type
        from app.models.models import Payment

        async with info.context.session_factory() as db:
            q = select(Payment).where(Payment.customer_id == self.customer_id)
            q = apply_int_filter(q, Payment.payment_id, filter.payment_id)
            q = apply_float_filter(q, Payment.amount, filter.amount)
            q = apply_datetime_filter(q, Payment.payment_date, filter.payment_date)
            q = apply_int_filter(q, Payment.rental_id, filter.rental_id)
            result = await db.execute(q)
            return [_payment_to_type(p) for p in result.scalars().all()]


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
