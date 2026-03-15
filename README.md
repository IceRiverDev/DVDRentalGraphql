# DVDRental GraphQL API

A standalone **FastAPI + Strawberry GraphQL** service that exposes the DVD Rental PostgreSQL database via a fully-typed GraphQL API, with JWT-based authentication via Keycloak.

## Tech Stack

| Layer | Library |
|---|---|
| Web framework | FastAPI |
| GraphQL | Strawberry GraphQL |
| ORM | SQLAlchemy 2.x (async) |
| DB driver | asyncpg |
| Auth | Keycloak (JWT / JWKS) |
| Python | 3.13+ |

## Requirements

- Python 3.13+
- PostgreSQL with the `dvdrental` database loaded
- Keycloak instance configured with the `dvd-rental` realm

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # fill in DB / Keycloak settings
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

Interactive playground (GraphiQL): **http://localhost:8001/graphql**

---

## Authentication

All GraphQL requests require a valid Keycloak Bearer token:

```
Authorization: Bearer <access_token>
```

Obtain a token:

```bash
curl -X POST http://localhost:8090/realms/dvd-rental/protocol/openid-connect/token \
  -d "grant_type=password&client_id=dvd-rental-api&username=<user>&password=<pass>"
```

---

## Filter Operators

All collection queries and sub-fields support rich per-field filter operators.

### `StringFilter`

| Operator | SQL equivalent | Example |
|---|---|---|
| `eq` | `= 'x'` | `{ eq: "ACADEMY DINOSAUR" }` |
| `neq` | `!= 'x'` | `{ neq: "ACADEMY DINOSAUR" }` |
| `like` | `LIKE 'x'` (case-sensitive) | `{ like: "%DINO%" }` |
| `ilike` | `ILIKE 'x'` (case-insensitive) | `{ ilike: "%dino%" }` |
| `contains` | `ILIKE '%x%'` (shorthand) | `{ contains: "dino" }` |
| `startsWith` | `ILIKE 'x%'` | `{ startsWith: "AC" }` |
| `endsWith` | `ILIKE '%x'` | `{ endsWith: "tion" }` |
| `in_` | `IN (...)` | `{ in_: ["G", "PG"] }` |
| `isNull` | `IS NULL` / `IS NOT NULL` | `{ isNull: true }` |

### `IntFilter`

`eq` · `neq` · `gt` · `gte` · `lt` · `lte` · `in_` · `isNull`

### `FloatFilter`

`eq` · `neq` · `gt` · `gte` · `lt` · `lte` · `isNull`

### `DateTimeFilter`

`eq` · `gt` · `gte` · `lt` · `lte` · `isNull` — values as ISO 8601 strings

### `DateFilter`

`eq` · `gt` · `gte` · `lt` · `lte` — values as `YYYY-MM-DD` strings

---

## Available Top-Level Queries

| Query | Description |
|---|---|
| `films` | Paginated film list with filter + sort |
| `film(filmId)` | Single film by ID |
| `actors` | Paginated actor list |
| `actor(actorId)` | Single actor |
| `customers` | Paginated customer list |
| `customer(customerId)` | Single customer |
| `rentals` | Paginated rental list |
| `rental(rentalId)` | Single rental |
| `overdueRentals` | Currently overdue rentals |
| `payments` | Paginated payment list |
| `payment(paymentId)` | Single payment |
| `paymentSummary` | Aggregate stats (count, sum, avg, min, max) |
| `inventories` | Paginated inventory list |
| `inventory(inventoryId)` | Single inventory item |
| `categories` | All categories |
| `languages` | All languages |
| `countries` | All countries |
| `stores` | All stores |

---

## Relation Graph

Every entity supports navigation in **both directions**. The arrows show what
nested fields are available on each type:

```
Language ──► films[]
   │
Category ──► films[]
   │
Film ──► language
     ──► actors[]
     ──► categories[]
     ──► inventories[]
         └── rentals[]
                └── customer
                └── payments[]

Actor ──► films[]

Customer ──► rentals[]
         └── payments[]

Rental ──► inventory ──► film
       ──► customer
       ──► payments[]

Payment ──► customer
        ──► rental
```

---

## Sub-field Filters

Every nested relation field accepts an optional `filter` argument using the
same filter types as top-level queries:

```graphql
# Sub-field filter syntax
type.relation(filter: <FilterType>) { ... }
```

Supported sub-field filters:

| Parent type | Sub-field | Filter type |
|---|---|---|
| `FilmType` | `actors` | `ActorFilter` |
| `FilmType` | `categories` | `CategoryFilter` |
| `FilmType` | `inventories` | `InventoryFilter` |
| `ActorType` | `films` | `FilmFilter` |
| `CategoryType` | `films` | `FilmFilter` |
| `LanguageType` | `films` | `FilmFilter` |
| `CustomerType` | `rentals` | `RentalFilter` |
| `CustomerType` | `payments` | `PaymentFilter` |
| `InventoryType` | `rentals` | `RentalFilter` |
| `RentalType` | `payments` | `PaymentFilter` |

> **Performance note:** When `filter` is omitted, the sub-field uses a
> **DataLoader** (all parent items batched into a single SQL `IN` query —
> no N+1). When a `filter` is provided, a **direct scoped query** is issued
> per parent item. Keep `pageSize` small (≤ 20) when using sub-field filters
> on large result sets.

---

## Example Queries

### Basic film search

```graphql
query {
  films(filter: { title: { contains: "love" } }, page: 1, pageSize: 10) {
    items { filmId title rating rentalRate }
    pageInfo { total hasNext }
  }
}
```

### Range + multi-condition

```graphql
query {
  films(
    filter: {
      rating: PG
      length: { gte: 90, lte: 120 }
      rentalRate: { gte: 4.0 }
    }
    sort: { field: LENGTH, direction: ASC }
    page: 1
    pageSize: 10
  ) {
    items { title rating length rentalRate }
    pageInfo { total }
  }
}
```

### Nested relations (no filter)

```graphql
query {
  film(filmId: 1) {
    title description rating
    language { name }
    actors { firstName lastName }
    categories { name }
  }
}
```

### Unretured rentals for a customer

```graphql
query {
  rentals(
    filter: { customerId: { eq: 5 }, isReturned: false }
    sort: { field: RENTAL_DATE, direction: DESC }
  ) {
    items { rentalId rentalDate returnDate }
    pageInfo { total }
  }
}
```

### Payments with aggregate summary (parallel queries)

```graphql
query {
  payments(
    filter: {
      paymentDate: { gte: "2007-04-01T00:00:00", lte: "2007-04-30T23:59:59" }
      amount: { gte: 5.0 }
    }
    sort: { field: AMOUNT, direction: DESC }
    page: 1 pageSize: 10
  ) {
    items { paymentId amount paymentDate }
    pageInfo { total }
  }
  paymentSummary {
    totalCount totalAmount averageAmount
  }
}
```

---

## Advanced Queries — Sub-field Filters & Reverse Relations

### Reverse: actor → their PG-rated films

```graphql
query {
  actors(
    filter: { lastName: { startsWith: "W" } }
    page: 1
    pageSize: 5
  ) {
    items {
      actorId firstName lastName
      films(filter: { rating: PG, length: { lte: 100 } }) {
        title rating length
      }
    }
  }
}
```

### Reverse: category → films by title keyword

```graphql
query {
  categories {
    categoryId name
    films(filter: { title: { ilike: "%action%" } }) {
      title rating rentalRate
    }
  }
}
```

### Film → filtered inventories (available stock in store 1)

```graphql
query {
  films(
    filter: { title: { contains: "academy" } }
    page: 1 pageSize: 3
  ) {
    items {
      title
      inventories(filter: { storeId: { eq: 1 }, isAvailable: true }) {
        inventoryId storeId
      }
    }
  }
}
```

### Customer full history — rentals not yet returned + large payments

```graphql
query {
  customers(
    filter: { customerId: { eq: 148 } }
    page: 1 pageSize: 1
  ) {
    items {
      firstName lastName email
      rentals(filter: { isReturned: false }) {
        rentalId rentalDate
        inventory { film { title } }
      }
      payments(filter: { amount: { gte: 7.0 } }) {
        paymentId amount paymentDate
      }
    }
  }
}
```

### Deep chain: inventory → rental history for a specific film

```graphql
query {
  inventories(
    filter: { filmId: { eq: 1 }, storeId: { eq: 1 } }
    page: 1 pageSize: 5
  ) {
    items {
      inventoryId storeId
      film { title }
      rentals(filter: { isReturned: true, rentalDate: { gte: "2005-07-01T00:00:00" } }) {
        rentalId rentalDate returnDate
        customer { firstName lastName }
        payments { amount }
      }
    }
  }
}
```

### Payment → back to customer and rental (reverse traversal)

```graphql
query {
  payments(
    filter: { amount: { gte: 9.0 } }
    sort: { field: AMOUNT, direction: DESC }
    page: 1 pageSize: 5
  ) {
    items {
      paymentId amount paymentDate
      customer { firstName lastName email }
      rental {
        rentalDate returnDate
        inventory { film { title rating } }
      }
    }
  }
}
```

### Language → long English films available in store 2

```graphql
query {
  languages {
    languageId name
    films(filter: { length: { gte: 150 }, rating: R }) {
      title length rating
      inventories(filter: { storeId: { eq: 2 } }) {
        inventoryId
      }
    }
  }
}
```

---

## Docker

```bash
docker build -t dvd-rental-graphql .
docker run -p 8001:8001 --env-file .env dvd-rental-graphql
```

---

## Directory Structure

```
app/
├── core/
│   ├── config.py            # Settings (pydantic-settings)
│   ├── database.py          # Async SQLAlchemy engine + session factory
│   └── security.py          # Keycloak JWT verification (JWKS)
├── models/
│   └── models.py            # SQLAlchemy ORM models
└── graphql/
    ├── types/               # Strawberry @type output types
    │   ├── film.py          # FilmType (actors/categories/inventories with sub-filter)
    │   ├── catalog.py       # ActorType, CategoryType, LanguageType (films with sub-filter)
    │   ├── people.py        # CustomerType (rentals/payments with sub-filter)
    │   ├── geography.py     # AddressType, CityType, CountryType
    │   ├── transactions.py  # InventoryType, RentalType, PaymentType (sub-filters)
    │   └── common.py        # PageInfo
    ├── filters/
    │   ├── shared.py        # MpaaRatingEnum, CategoryFilter, StringFilter, IntFilter,
    │   │                    # FloatFilter, DateTimeFilter, DateFilter + apply helpers
    │   ├── film_filter.py   # FilmFilter, FilmConnection
    │   ├── actor_filter.py  # ActorFilter, ActorConnection
    │   ├── customer_filter.py
    │   ├── rental_filter.py
    │   ├── payment_filter.py
    │   └── inventory_filter.py
    ├── resolvers/
    │   └── query.py         # All top-level @strawberry.field resolvers
    ├── context.py           # GraphQLContext (session_factory, loaders, user)
    ├── dataloaders.py       # 16 DataLoader batch functions (N+1 prevention)
    └── schema.py            # strawberry.Schema definition
tests/
├── conftest.py              # Shared fixtures, mock session factory
├── test_filters.py          # Pure unit tests for all apply_* helpers
├── test_schema.py           # Schema-level integration tests (mocked DB)
└── test_auth.py             # JWT auth unit tests
```

---

## Architecture: How a Query Flows Through the Code

This section walks through two examples end-to-end — a simple top-level query
and a sub-field filtered query — so that anyone maintaining this codebase can
understand every layer.

---

### Example A — Top-level query with filters

```graphql
query {
  films(
    filter: { rating: PG, length: { gte: 90, lte: 120 } }
    page: 1
    pageSize: 5
  ) {
    items {
      title rating length
      language { name }
      actors { firstName lastName }
    }
    pageInfo { total }
  }
}
```

#### Step 1 — HTTP request → FastAPI → context

FastAPI receives `POST /graphql`. Before GraphQL executes anything, `get_context`
in `main.py` runs:

```python
# app/main.py
async def get_context(request: Request) -> GraphQLContext:
    current_user = await get_current_user_from_request(request)  # validate JWT
    return GraphQLContext(
        session_factory=AsyncSessionLocal,   # factory, NOT a session instance
        current_user=current_user,
        loaders=DataLoaders(),               # fresh loaders per request
    )
```

Key design choice: `session_factory` is passed, not an open session. Each
resolver creates its own independent session to avoid SQLAlchemy's
"concurrent operations not permitted" error (Strawberry resolves multiple
fields in parallel).

#### Step 2 — Schema routes to a resolver

Strawberry matches the `films` top-level field to `Query.films`:

```python
# app/graphql/resolvers/query.py
@strawberry.type
class Query:
    @strawberry.field
    async def films(
        self,
        info: Info,                           # framework-injected — carries context
        filter: Optional[FilmFilter] = None,  # deserialised from { rating: PG, length: {...} }
        sort: Optional[FilmSort] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> FilmConnection:
        ...
```

Strawberry auto-deserialises the JSON `filter` object into the `FilmFilter`
Python class before calling the method.

#### Step 3 — `@strawberry.input` defines the filter shape

```python
# app/graphql/filters/film_filter.py
@strawberry.input          # input = argument type (never returned)
class FilmFilter:
    rating: Optional[MpaaRatingEnum] = None   # PG
    length: Optional[IntFilter] = None         # { gte: 90, lte: 120 }
    ...

# app/graphql/filters/shared.py
@strawberry.input
class IntFilter:
    gte: Optional[int] = None   # ← 90
    lte: Optional[int] = None   # ← 120
    ...
```

> **Rule of thumb:**
> `@strawberry.input` = data coming **in** (arguments, filters).
> `@strawberry.type`  = data going **out** (response fields).

#### Step 4 — Resolver builds and runs the SQL query

```python
async with info.context.session_factory() as db:   # independent session
    q = select(Film)

    if filter.rating is not None:
        q = q.where(Film.rating == OrmRating(filter.rating.value))

    # apply_int_filter translates IntFilter → SQLAlchemy .where() clauses
    q = apply_int_filter(q, Film.length, filter.length)
    # → Film.length >= 90 AND Film.length <= 120

    count = (await db.execute(select(func.count()).select_from(q))).scalar_one()
    rows  = (await db.execute(q.offset((page-1)*page_size).limit(page_size))).scalars().all()
```

`apply_int_filter` in `shared.py`:

```python
def apply_int_filter(q, column, f):
    if f is None: return q
    if f.gte is not None: q = q.where(column >= f.gte)
    if f.lte is not None: q = q.where(column <= f.lte)
    ...
    return q
```

#### Step 5 — `@strawberry.type` defines the response shape

```python
# app/graphql/filters/film_filter.py
@strawberry.type           # type = return type (never used as argument)
class FilmConnection:
    items:     List[FilmType]
    page_info: PageInfo
```

Only the fields the client asked for are serialised. Fields not in the
query selection are never loaded.

#### Step 6 — Nested fields trigger DataLoaders

`language { name }` and `actors { firstName lastName }` are `@strawberry.field`
methods on `FilmType`. Strawberry calls them **concurrently** for every film:

```python
# app/graphql/types/film.py
@strawberry.type
class FilmType:
    ...
    @strawberry.field
    async def language(self, info: Info) -> Optional[LanguageType]:
        # DataLoader: collects all language_id values across all films
        # then fires ONE query: SELECT … WHERE language_id IN (1, 2, 3)
        return await info.context.loaders.language.load(self.language_id)

    @strawberry.field
    async def actors(self, info: Info, filter: Optional[ActorFilter] = None) -> List[ActorType]:
        if filter is None:
            # ✅ No filter → DataLoader (batched, no N+1)
            return await info.context.loaders.film_actors.load(self.film_id)
        # ❗ Filter provided → direct scoped query (see Example B below)
        ...
```

#### Step 7 — DataLoader batches N queries into 1

```python
# app/graphql/dataloaders.py
async def _load_languages(self, ids: Sequence[int]) -> list[LanguageType | None]:
    async with self._session_factory() as db:    # own session per batch
        result = await db.execute(
            select(Language).where(Language.language_id.in_(ids))
            # ids = [1, 1, 1, 2, 1] collected from all 5 films
            # → single SQL: WHERE language_id IN (1, 2)
        )
        mapping = {l.language_id: _language_to_type(l) for l in result.scalars()}
    return [mapping.get(id_) for id_ in ids]
```

Each DataLoader batch opens its **own session** — this is essential because
multiple batches may run concurrently.

#### Full flow diagram (Example A)

```
POST /graphql
    │
    ▼ main.py – get_context()
    │   validate JWT  →  current_user
    │   DataLoaders()
    │   session_factory = AsyncSessionLocal
    │
    ▼ strawberry.Schema → Query.films(filter, page, pageSize)
    │   async with session_factory() as db:
    │       SELECT … WHERE rating='PG' AND length BETWEEN 90 AND 120
    │       → FilmConnection { items: [FilmType×5], pageInfo }
    │
    ▼ Strawberry resolves nested fields (concurrently per film)
    │
    ├── FilmType.language  → loaders.language.load(language_id)
    │                            └── batch: SELECT language WHERE id IN (1,…)
    │
    └── FilmType.actors    → loaders.film_actors.load(film_id)
                                 └── batch: SELECT actor JOIN film_actor WHERE film_id IN (…)
```

---

### Example B — Sub-field filter

```graphql
query {
  actors(page: 1, pageSize: 3) {
    items {
      firstName lastName
      films(filter: { rating: PG, title: { ilike: "%love%" } }) {
        title rating
      }
    }
  }
}
```

The key difference from Example A: the `films` field carries a `filter`
argument. This changes how the sub-field resolver behaves.

#### How ActorType.films decides what to do

```python
# app/graphql/types/catalog.py
@strawberry.field
async def films(
    self,
    info: Info,
    filter: Optional[FilmFilter] = None,
) -> List[FilmType]:

    if filter is None:
        # ✅ No filter → DataLoader path
        # All 3 actors' film_ids are batched:
        # SELECT film JOIN film_actor WHERE actor_id IN (1, 2, 3)
        return await info.context.loaders.actor_films.load(self.actor_id)

    # ❗ Filter provided → scoped direct query for THIS actor only
    async with info.context.session_factory() as db:
        q = (
            select(Film)
            .join(FilmActor, FilmActor.film_id == Film.film_id)
            .where(FilmActor.actor_id == self.actor_id)   # ← scope to this actor
        )
        q = _apply_film_filter(q, filter)
        # → adds: AND film.rating='PG' AND film.title ILIKE '%love%'
        result = await db.execute(q)
        return [_film_to_type(f) for f in result.scalars().all()]
```

**Why not always use DataLoader?**
DataLoader works by batching identical operations. With a filter, each parent
might theoretically have different filters, making batching impossible. The
trade-off is explicit:

| | No filter | With filter |
|---|---|---|
| SQL queries | 1 (batched `IN`) | N (one per parent item) |
| Use case | Default — always efficient | When you need to narrow results |
| Mitigation | — | Keep top-level `pageSize` small |

---

### How circular imports were resolved

Filter files originally imported type files (e.g., `actor_filter.py` imported
`ActorType` from `catalog.py`). When type files needed to import filter files
back (for sub-field filter arguments), it created a cycle:

```
# The cycle (before fix)
catalog.py → film_filter.py → film.py → actor_filter.py → catalog.py
                 ↑_______________________________________________|
```

**Fix: replace runtime imports in filter files with `strawberry.lazy()`**

```python
# Before — runtime import, creates the cycle
from app.graphql.types.catalog import ActorType

@strawberry.type
class ActorConnection:
    items: List[ActorType]          # ← triggers import at module load

# After — deferred resolution, no runtime import
@strawberry.type
class ActorConnection:
    items: List[Annotated[
        "ActorType",
        strawberry.lazy("app.graphql.types.catalog")   # ← resolved at schema build time
    ]]
```

`strawberry.lazy()` tells Strawberry: "don't resolve this type now; look it up
when you build the schema." By that time all modules are fully loaded, so no
cycle occurs.

Additionally, `MpaaRatingEnum` was moved from `film.py` to `shared.py`, so
`film_filter.py` no longer imports `film.py` at all:

```
# After fix — filter files only depend on shared.py (no type files)
film_filter.py   → shared.py   ✅
actor_filter.py  → shared.py   ✅
rental_filter.py → shared.py   ✅
...

# Type files can now safely import filter files at module level
catalog.py  → film_filter.py   ✅ (no cycle)
film.py     → actor_filter.py  ✅ (no cycle)
people.py   → rental_filter.py ✅ (no cycle)
```

---

### Strawberry keyword reference

| Keyword | Where | Purpose |
|---|---|---|
| `@strawberry.type` | Class | Defines a **response** object (returned to client) |
| `@strawberry.input` | Class | Defines an **argument** object (sent by client) |
| `@strawberry.field` | Method | Marks a method as a GraphQL field with custom resolver |
| `@strawberry.enum` | Enum class | Exposes a Python enum as a GraphQL enum |
| `strawberry.lazy(…)` | Type annotation | Defers type lookup to break circular imports |
| `Info` | Parameter type | Framework object giving access to `context` (session_factory, loaders, user) |
| `DataLoader` | Class | Batches multiple `.load(key)` calls into one SQL `IN` query |
