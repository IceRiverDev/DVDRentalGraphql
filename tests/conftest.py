"""Shared fixtures for DVDRentalGraphql tests.

Strategy
--------
Resolvers open their own sessions via ``info.context.session_factory()``.
In tests we replace the factory with an async context-manager that yields
a pre-configured ``AsyncMock`` session, so no real database is needed.

DataLoaders also use ``AsyncSessionLocal`` internally; we patch that at the
module level so loader batches never touch a real DB.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.graphql.context import GraphQLContext
from app.graphql.dataloaders import DataLoaders


# ---------------------------------------------------------------------------
# Helpers to build fake ORM-like objects
# ---------------------------------------------------------------------------

def make_film(
    film_id: int = 1,
    title: str = "Test Film",
    rating_value: str = "PG",
    length: int = 90,
    rental_rate: float = 2.99,
    language_id: int = 1,
) -> MagicMock:
    from app.models.models import MpaaRating

    film = MagicMock()
    film.film_id = film_id
    film.title = title
    film.description = "A test description"
    film.release_year = 2005
    film.language_id = language_id
    film.rental_duration = 3
    film.rental_rate = Decimal(str(rental_rate))
    film.length = length
    film.replacement_cost = Decimal("19.99")
    film.rating = MpaaRating(rating_value)
    film.special_features = None
    film.last_update = datetime(2020, 1, 1)
    return film


def make_actor(actor_id: int = 1, first_name: str = "John", last_name: str = "Doe") -> MagicMock:
    actor = MagicMock()
    actor.actor_id = actor_id
    actor.first_name = first_name
    actor.last_name = last_name
    actor.last_update = datetime(2020, 1, 1)
    return actor


def make_customer(customer_id: int = 1, first_name: str = "Alice", last_name: str = "Smith") -> MagicMock:
    customer = MagicMock()
    customer.customer_id = customer_id
    customer.store_id = 1
    customer.first_name = first_name
    customer.last_name = last_name
    customer.email = f"{first_name.lower()}@example.com"
    customer.address_id = 1
    customer.activebool = True
    customer.create_date = datetime(2020, 1, 1).date()
    customer.last_update = datetime(2020, 1, 1)
    customer.active = 1
    return customer


def make_rental(rental_id: int = 1, customer_id: int = 1, inventory_id: int = 1) -> MagicMock:
    rental = MagicMock()
    rental.rental_id = rental_id
    rental.rental_date = datetime(2005, 6, 14, 23, 41, 0)
    rental.inventory_id = inventory_id
    rental.customer_id = customer_id
    rental.return_date = datetime(2005, 6, 18, 0, 0, 0)
    rental.staff_id = 1
    rental.last_update = datetime(2020, 1, 1)
    return rental


def make_payment(payment_id: int = 1, customer_id: int = 1, amount: float = 3.99) -> MagicMock:
    payment = MagicMock()
    payment.payment_id = payment_id
    payment.customer_id = customer_id
    payment.staff_id = 1
    payment.rental_id = 1
    payment.amount = Decimal(str(amount))
    payment.payment_date = datetime(2007, 4, 5, 12, 0, 0)
    return payment


def make_inventory(inventory_id: int = 1, film_id: int = 1, store_id: int = 1) -> MagicMock:
    inv = MagicMock()
    inv.inventory_id = inventory_id
    inv.film_id = film_id
    inv.store_id = store_id
    inv.last_update = datetime(2020, 1, 1)
    return inv


# ---------------------------------------------------------------------------
# Mock DB session factory
# ---------------------------------------------------------------------------

def build_session(rows: list[Any], total: int) -> AsyncMock:
    """Return an AsyncMock session whose execute() alternates between a
    COUNT result (first call) and a rows result (subsequent calls)."""

    count_result = MagicMock()
    count_result.scalar_one.return_value = total

    rows_result = MagicMock()
    rows_result.scalars.return_value.all.return_value = rows

    session = AsyncMock()
    session.execute = AsyncMock(side_effect=[count_result, rows_result])
    return session


def make_session_factory(rows: list[Any], total: int | None = None):
    """Create an async context-manager factory backed by a mock session."""
    session = build_session(rows, total if total is not None else len(rows))

    @asynccontextmanager
    async def _factory():
        yield session

    return _factory, session


# ---------------------------------------------------------------------------
# GraphQLContext factory
# ---------------------------------------------------------------------------

def make_context(rows: list[Any], total: int | None = None) -> tuple[GraphQLContext, AsyncMock]:
    factory, session = make_session_factory(rows, total)
    loaders = DataLoaders()
    ctx = GraphQLContext(
        session_factory=factory,
        current_user={"sub": "test-user", "preferred_username": "tester"},
        loaders=loaders,
    )
    return ctx, session
