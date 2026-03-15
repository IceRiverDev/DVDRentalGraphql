"""Schema-level integration tests for GraphQL resolvers.

These tests invoke ``schema.execute()`` directly with a fake context whose
``session_factory`` yields an ``AsyncMock`` session.  No real database or
network calls are made.

Because each resolver calls ``db.execute()`` **twice** (once for the COUNT,
once for the rows), the mock uses ``side_effect`` to return different values
on each invocation.
"""
from __future__ import annotations

from app.graphql.schema import schema
from tests.conftest import (
    make_actor,
    make_context,
    make_customer,
    make_film,
    make_inventory,
    make_payment,
    make_rental,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

async def _exec(query: str, ctx, variables: dict | None = None):
    """Execute a GraphQL query and assert no errors."""
    result = await schema.execute(query, context_value=ctx, variable_values=variables)
    assert result.errors is None, result.errors
    return result.data


# ===========================================================================
# Films
# ===========================================================================

class TestFilmsQuery:
    BASIC_QUERY = """
    query {
        films(page: 1, pageSize: 5) {
            items { filmId title }
            pageInfo { total page pageSize totalPages }
        }
    }
    """

    async def test_basic_returns_films(self):
        films = [make_film(1, "ACADEMY DINOSAUR"), make_film(2, "ACE GOLDFINGER")]
        ctx, _ = make_context(films, total=2)
        data = await _exec(self.BASIC_QUERY, ctx)
        items = data["films"]["items"]
        assert len(items) == 2
        assert items[0]["filmId"] == 1
        assert items[0]["title"] == "ACADEMY DINOSAUR"

    async def test_page_info(self):
        films = [make_film()]
        ctx, _ = make_context(films, total=10)
        data = await _exec(self.BASIC_QUERY, ctx)
        pi = data["films"]["pageInfo"]
        assert pi["total"] == 10
        assert pi["page"] == 1
        assert pi["pageSize"] == 5
        assert pi["totalPages"] == 2

    TITLE_FILTER_QUERY = """
    query FilmsFilterTitle($filter: FilmFilter!) {
        films(page: 1, pageSize: 10, filter: $filter) {
            items { filmId title }
            pageInfo { total }
        }
    }
    """

    async def test_title_string_filter_like(self):
        films = [make_film(1, "ACADEMY DINOSAUR")]
        ctx, session = make_context(films, total=1)
        data = await _exec(
            self.TITLE_FILTER_QUERY,
            ctx,
            variables={"filter": {"title": {"like": "%ACAD%"}}},
        )
        assert data["films"]["items"][0]["title"] == "ACADEMY DINOSAUR"

    async def test_title_ilike_filter(self):
        films = [make_film(3, "ALIEN CENTER")]
        ctx, _ = make_context(films, total=1)
        data = await _exec(
            self.TITLE_FILTER_QUERY,
            ctx,
            variables={"filter": {"title": {"ilike": "%alien%"}}},
        )
        assert len(data["films"]["items"]) == 1

    LENGTH_FILTER_QUERY = """
    query FilmsFilterLength($filter: FilmFilter!) {
        films(page: 1, pageSize: 10, filter: $filter) {
            items { filmId title length }
            pageInfo { total }
        }
    }
    """

    async def test_length_range_int_filter(self):
        films = [make_film(1, "SHORT FILM", length=60), make_film(2, "MED FILM", length=90)]
        ctx, _ = make_context(films, total=2)
        data = await _exec(
            self.LENGTH_FILTER_QUERY,
            ctx,
            variables={"filter": {"length": {"gte": 60, "lte": 100}}},
        )
        assert len(data["films"]["items"]) == 2

    FILM_ID_FILTER_QUERY = """
    query FilmsById($filter: FilmFilter!) {
        films(page: 1, pageSize: 1, filter: $filter) {
            items { filmId title }
            pageInfo { total }
        }
    }
    """

    async def test_film_id_filter(self):
        films = [make_film(42, "SPECIFIC FILM")]
        ctx, _ = make_context(films, total=1)
        data = await _exec(
            self.FILM_ID_FILTER_QUERY,
            ctx,
            variables={"filter": {"filmId": {"eq": 42}}},
        )
        assert data["films"]["items"][0]["filmId"] == 42

    RATING_FILTER_QUERY = """
    query FilmsRating($filter: FilmFilter!) {
        films(page: 1, pageSize: 10, filter: $filter) {
            items { filmId rating }
            pageInfo { total }
        }
    }
    """

    async def test_rating_enum_filter(self):
        films = [make_film(1, "PG FILM", rating_value="PG")]
        ctx, _ = make_context(films, total=1)
        data = await _exec(
            self.RATING_FILTER_QUERY,
            ctx,
            variables={"filter": {"rating": "PG"}},
        )
        assert data["films"]["items"][0]["rating"] == "PG"

    async def test_empty_results(self):
        ctx, _ = make_context([], total=0)
        data = await _exec(self.BASIC_QUERY, ctx)
        assert data["films"]["items"] == []
        assert data["films"]["pageInfo"]["total"] == 0


# ===========================================================================
# Actors
# ===========================================================================

class TestActorsQuery:
    BASIC_QUERY = """
    query {
        actors(page: 1, pageSize: 5) {
            items { actorId firstName lastName }
            pageInfo { total }
        }
    }
    """

    async def test_basic_returns_actors(self):
        actors = [make_actor(1, "PENELOPE", "GUINESS"), make_actor(2, "NICK", "WAHLBERG")]
        ctx, _ = make_context(actors, total=2)
        data = await _exec(self.BASIC_QUERY, ctx)
        assert len(data["actors"]["items"]) == 2
        assert data["actors"]["items"][0]["firstName"] == "PENELOPE"

    NAME_FILTER_QUERY = """
    query ActorsByName($filter: ActorFilter!) {
        actors(page: 1, pageSize: 10, filter: $filter) {
            items { actorId firstName lastName }
            pageInfo { total }
        }
    }
    """

    async def test_first_name_filter(self):
        actors = [make_actor(1, "PENELOPE", "GUINESS")]
        ctx, _ = make_context(actors, total=1)
        data = await _exec(
            self.NAME_FILTER_QUERY,
            ctx,
            variables={"filter": {"firstName": {"ilike": "%penelope%"}}},
        )
        assert data["actors"]["items"][0]["firstName"] == "PENELOPE"

    async def test_actor_id_filter(self):
        actors = [make_actor(7, "GRACE", "MOSTEL")]
        ctx, _ = make_context(actors, total=1)
        data = await _exec(
            self.NAME_FILTER_QUERY,
            ctx,
            variables={"filter": {"actorId": {"eq": 7}}},
        )
        assert data["actors"]["items"][0]["actorId"] == 7


# ===========================================================================
# Customers
# ===========================================================================

class TestCustomersQuery:
    BASIC_QUERY = """
    query {
        customers(page: 1, pageSize: 5) {
            items { customerId firstName lastName email activebool }
            pageInfo { total }
        }
    }
    """

    async def test_basic_returns_customers(self):
        customers = [make_customer(1, "MARY", "SMITH"), make_customer(2, "PATRICIA", "JOHNSON")]
        ctx, _ = make_context(customers, total=2)
        data = await _exec(self.BASIC_QUERY, ctx)
        assert len(data["customers"]["items"]) == 2
        assert data["customers"]["items"][0]["email"] == "mary@example.com"

    async def test_active_filter(self):
        customers = [make_customer(1, "MARY", "SMITH")]
        ctx, _ = make_context(customers, total=1)
        data = await _exec(
            """
            query {
                customers(page:1, pageSize:10, filter:{active: true}) {
                    items { customerId activebool }
                    pageInfo { total }
                }
            }
            """,
            ctx,
        )
        assert data["customers"]["items"][0]["activebool"] is True


# ===========================================================================
# Rentals
# ===========================================================================

class TestRentalsQuery:
    BASIC_QUERY = """
    query {
        rentals(page: 1, pageSize: 5) {
            items { rentalId rentalDate returnDate }
            pageInfo { total }
        }
    }
    """

    async def test_basic_returns_rentals(self):
        rentals = [make_rental(1), make_rental(2)]
        ctx, _ = make_context(rentals, total=2)
        data = await _exec(self.BASIC_QUERY, ctx)
        assert len(data["rentals"]["items"]) == 2
        assert data["rentals"]["items"][0]["rentalId"] == 1

    async def test_is_returned_true_filter(self):
        """returnDate IS NOT NULL means the DVD was returned."""
        rentals = [make_rental(1)]
        ctx, _ = make_context(rentals, total=1)
        data = await _exec(
            """
            query {
                rentals(page:1, pageSize:5, filter:{isReturned: true}) {
                    items { rentalId returnDate }
                    pageInfo { total }
                }
            }
            """,
            ctx,
        )
        assert data["rentals"]["items"][0]["rentalId"] == 1

    async def test_rental_id_filter(self):
        rentals = [make_rental(99)]
        ctx, _ = make_context(rentals, total=1)
        data = await _exec(
            """
            query {
                rentals(page:1, pageSize:1, filter:{rentalId:{eq:99}}) {
                    items { rentalId }
                    pageInfo { total }
                }
            }
            """,
            ctx,
        )
        assert data["rentals"]["items"][0]["rentalId"] == 99


# ===========================================================================
# Payments
# ===========================================================================

class TestPaymentsQuery:
    BASIC_QUERY = """
    query {
        payments(page: 1, pageSize: 5) {
            items { paymentId amount paymentDate }
            pageInfo { total }
        }
    }
    """

    async def test_basic_returns_payments(self):
        payments = [make_payment(1, amount=2.99), make_payment(2, amount=4.99)]
        ctx, _ = make_context(payments, total=2)
        data = await _exec(self.BASIC_QUERY, ctx)
        assert len(data["payments"]["items"]) == 2

    async def test_amount_float_filter(self):
        payments = [make_payment(3, amount=9.99)]
        ctx, _ = make_context(payments, total=1)
        data = await _exec(
            """
            query {
                payments(page:1, pageSize:5, filter:{amount:{gte: 5.0}}) {
                    items { paymentId amount }
                    pageInfo { total }
                }
            }
            """,
            ctx,
        )
        assert data["payments"]["items"][0]["paymentId"] == 3

    async def test_payment_id_filter(self):
        payments = [make_payment(55)]
        ctx, _ = make_context(payments, total=1)
        data = await _exec(
            """
            query {
                payments(page:1, pageSize:1, filter:{paymentId:{eq:55}}) {
                    items { paymentId }
                    pageInfo { total }
                }
            }
            """,
            ctx,
        )
        assert data["payments"]["items"][0]["paymentId"] == 55


# ===========================================================================
# Inventories
# ===========================================================================

class TestInventoriesQuery:
    BASIC_QUERY = """
    query {
        inventories(page: 1, pageSize: 5) {
            items { inventoryId filmId storeId }
            pageInfo { total }
        }
    }
    """

    async def test_basic_returns_inventories(self):
        inventories = [make_inventory(1, film_id=1), make_inventory(2, film_id=2)]
        ctx, _ = make_context(inventories, total=2)
        data = await _exec(self.BASIC_QUERY, ctx)
        assert len(data["inventories"]["items"]) == 2

    async def test_store_id_filter(self):
        inventories = [make_inventory(5, film_id=3, store_id=2)]
        ctx, _ = make_context(inventories, total=1)
        data = await _exec(
            """
            query {
                inventories(page:1, pageSize:5, filter:{storeId: {eq: 2}}) {
                    items { inventoryId storeId }
                    pageInfo { total }
                }
            }
            """,
            ctx,
        )
        assert data["inventories"]["items"][0]["storeId"] == 2
