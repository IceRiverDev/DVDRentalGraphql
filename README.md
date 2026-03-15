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
# Create and activate virtualenv
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and fill in environment variables
cp .env.example .env

# Run the server
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

The interactive GraphQL playground (GraphiQL) is available at **http://localhost:8001/graphql**.

## Authentication

All GraphQL requests (except `GET /graphql` for the playground UI) require a valid Keycloak Bearer token:

```
Authorization: Bearer <access_token>
```

Obtain a token from Keycloak:

```bash
curl -X POST http://localhost:8090/realms/dvd-rental/protocol/openid-connect/token \
  -d "grant_type=password&client_id=dvd-rental-api&username=<user>&password=<pass>"
```

## Filter Operators

All collection queries support rich per-field filter operators.

### String fields — `StringFilter`

| Operator | Description |
|---|---|
| `eq` | Exact match |
| `neq` | Not equal |
| `like` | Case-sensitive LIKE (`%` as wildcard) |
| `ilike` | Case-insensitive LIKE |
| `contains` | Shorthand for `ilike %value%` |
| `startsWith` | Shorthand for `ilike value%` |
| `endsWith` | Shorthand for `ilike %value` |
| `in_` | Value is in list |
| `isNull` | `true` = IS NULL, `false` = IS NOT NULL |

### Integer fields — `IntFilter`

`eq` · `neq` · `gt` · `gte` · `lt` · `lte` · `in_` · `isNull`

### Float/Decimal fields — `FloatFilter`

`eq` · `neq` · `gt` · `gte` · `lt` · `lte` · `isNull`

### DateTime fields — `DateTimeFilter`

`eq` · `gt` · `gte` · `lt` · `lte` · `isNull` — values as ISO 8601 strings

### Date fields — `DateFilter`

`eq` · `gt` · `gte` · `lt` · `lte` — values as `YYYY-MM-DD` strings

## Available Queries

| Query | Description |
|---|---|
| `films` | Paginated film list with full filter + sort |
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

## Example Queries

### Simple film search

```graphql
query {
  films(
    filter: { title: { contains: "love" } }
    page: 1
    pageSize: 10
  ) {
    items { filmId title rating rentalRate }
    pageInfo { total hasNext }
  }
}
```

### Filter by ID

```graphql
query {
  films(filter: { filmId: { eq: 1 } }) {
    items { filmId title }
    pageInfo { total }
  }
}
```

### Range + multiple conditions

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

### Nested relations (language, actors, categories)

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

### Actor last name starts with "W"

```graphql
query {
  actors(
    filter: { lastName: { startsWith: "W" } }
    sort: { field: LAST_NAME, direction: ASC }
  ) {
    items { actorId firstName lastName }
    pageInfo { total }
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

### Payments in a date range with aggregate summary

```graphql
query {
  payments(
    filter: {
      paymentDate: { gte: "2007-04-01T00:00:00", lte: "2007-04-30T23:59:59" }
      amount: { gte: 5.0 }
    }
    sort: { field: AMOUNT, direction: DESC }
    page: 1
    pageSize: 10
  ) {
    items { paymentId amount paymentDate }
    pageInfo { total }
  }

  paymentSummary {
    totalCount totalAmount averageAmount minAmount maxAmount
  }
}
```

## Docker

```bash
docker build -t dvd-rental-graphql .
docker run -p 8001:8001 --env-file .env dvd-rental-graphql
```

## Directory Structure

```
app/
├── core/
│   ├── config.py       # Settings (pydantic-settings)
│   ├── database.py     # Async SQLAlchemy engine + session factory
│   └── security.py     # Keycloak JWT verification
├── models/
│   └── models.py       # SQLAlchemy ORM models
└── graphql/
    ├── types/          # Strawberry @type output types
    │   ├── film.py
    │   ├── catalog.py  # Actor, Category, Language
    │   ├── people.py   # Customer, Store
    │   ├── geography.py
    │   ├── transactions.py  # Rental, Payment, Inventory
    │   └── common.py   # PageInfo
    ├── filters/
    │   ├── shared.py        # StringFilter, IntFilter, FloatFilter,
    │   │                    # DateTimeFilter, DateFilter + apply helpers
    │   ├── film_filter.py
    │   ├── actor_filter.py
    │   ├── customer_filter.py
    │   ├── rental_filter.py
    │   ├── payment_filter.py
    │   └── inventory_filter.py
    ├── resolvers/
    │   └── query.py    # All @strawberry.field resolvers
    ├── context.py      # GraphQLContext (session_factory, loaders, user)
    ├── dataloaders.py  # DataLoader batch functions (N+1 prevention)
    └── schema.py       # strawberry.Schema definition
```

---

## Architecture: How a Query Flows Through the Code

This section walks through a concrete example end-to-end so that anyone
maintaining this codebase can understand every layer.

### Example query

```graphql
query {
  films(
    filter: { rating: PG, length: { gte: 90, lte: 120 } }
    page: 1
    pageSize: 5
  ) {
    items {
      title
      rating
      length
      language { name }
      actors { firstName lastName }
    }
    pageInfo { total }
  }
}
```

---

### Step 1 — HTTP request → FastAPI → context

FastAPI receives the `POST /graphql` request. Before anything GraphQL happens,
the `get_context` function in `main.py` is called:

```python
# app/main.py
async def get_context(request: Request) -> GraphQLContext:
    current_user = await get_current_user_from_request(request)  # validates JWT
    loaders = DataLoaders()                                       # creates fresh DataLoaders per request
    return GraphQLContext(
        session_factory=AsyncSessionLocal,  # no shared session – each resolver opens its own
        current_user=current_user,
        loaders=loaders,
    )
```

The context object is passed to every resolver in the request.

---

### Step 2 — Schema routes the query to a resolver

Strawberry reads the query, finds the `films` top-level field, and calls the
matching method on the `Query` class. The method is marked with
`@strawberry.field`:

```python
# app/graphql/resolvers/query.py
@strawberry.type
class Query:

    @strawberry.field
    async def films(
        self,
        info: Info,                           # framework-injected context
        filter: Optional[FilmFilter] = None,  # parsed from filter: { ... }
        sort: Optional[FilmSort] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> FilmConnection:                      # return type drives what fields are queryable
        ...
```

Strawberry automatically deserialises `filter: { rating: PG, length: { gte: 90, lte: 120 } }`
into a `FilmFilter` Python object before calling the method.

---

### Step 3 — `@strawberry.input` defines what the filter object looks like

`FilmFilter` is a Strawberry **input type** — a typed container for incoming
arguments:

```python
# app/graphql/filters/film_filter.py
@strawberry.input          # input = used only as an argument, never returned
class FilmFilter:
    film_id: Optional[IntFilter] = None
    title:   Optional[StringFilter] = None
    rating:  Optional[MpaaRatingEnum] = None
    length:  Optional[IntFilter] = None     # { gte: 90, lte: 120 } maps here
    ...
```

`IntFilter` is itself another `@strawberry.input`:

```python
# app/graphql/filters/shared.py
@strawberry.input
class IntFilter:
    eq:  Optional[int] = None
    gte: Optional[int] = None   # ← 90
    lte: Optional[int] = None   # ← 120
    ...
```

> **Rule of thumb:**
> `@strawberry.input` = data coming **in** (arguments).
> `@strawberry.type`  = data going **out** (response fields).

---

### Step 4 — Resolver opens its own DB session and builds the SQL query

Each resolver opens an **independent** `AsyncSession` to avoid concurrency
issues (Strawberry resolves multiple top-level fields in parallel).

```python
async with info.context.session_factory() as db:
    q = select(Film)

    if filter:
        # apply_int_filter translates IntFilter → SQLAlchemy .where() clauses
        q = apply_int_filter(q, Film.length, filter.length)
        # e.g. Film.length >= 90 AND Film.length <= 120

        if filter.rating is not None:
            q = q.where(Film.rating == OrmRating(filter.rating.value))
        ...
```

The `apply_*` helpers in `shared.py` are simple utilities that translate each
operator field into a `.where()` clause:

```python
def apply_int_filter(q, column, f):
    if f is None: return q
    if f.gte is not None: q = q.where(column >= f.gte)
    if f.lte is not None: q = q.where(column <= f.lte)
    ...
    return q
```

---

### Step 5 — `@strawberry.type` defines what the response looks like

The resolver returns a `FilmConnection`, which is a `@strawberry.type`:

```python
# app/graphql/filters/film_filter.py
@strawberry.type           # type = used only as a return value
class FilmConnection:
    items:     List[FilmType]
    page_info: PageInfo
```

The fields you ask for in the query (`items { ... }`, `pageInfo { total }`)
must exist on this type — otherwise Strawberry rejects the query at parse time.

---

### Step 6 — Nested fields trigger DataLoaders

You asked for `language { name }` and `actors { firstName lastName }`.
These are defined as `@strawberry.field` methods on `FilmType`:

```python
# app/graphql/types/film.py
@strawberry.type
class FilmType:
    film_id:  int
    title:    str
    rating:   Optional[MpaaRatingEnum]
    length:   Optional[int]
    ...

    @strawberry.field
    async def language(self, info: Info) -> Optional[LanguageType]:
        return await info.context.loaders.language.load(self.language_id)

    @strawberry.field
    async def actors(self, info: Info) -> List[ActorType]:
        return await info.context.loaders.film_actors.load(self.film_id)
```

Strawberry resolves `language` and `actors` **concurrently** for every film in
the result set. Without DataLoaders this would fire N×2 SQL queries.

---

### Step 7 — DataLoaders batch N queries into one

`DataLoader` collects all `load()` calls that happen in the same async tick
and fires a single batched SQL query:

```python
# app/graphql/dataloaders.py
async def _load_languages(self, ids: Sequence[int]) -> list[LanguageType | None]:
    async with self._session_factory() as db:          # own session per batch
        result = await db.execute(
            select(Language).where(Language.language_id.in_(ids))
            # ids = [1, 1, 1, 2, 1, ...] collected from all 5 films at once
            # → single SQL: WHERE language_id IN (1, 2)
        )
        mapping = {l.language_id: _language_to_type(l) for l in result.scalars()}
    return [mapping.get(id_) for id_ in ids]
```

Each DataLoader batch also opens its **own** `AsyncSession` to avoid the
"concurrent operations not permitted" error (SQLAlchemy async sessions are
not safe to use from multiple coroutines simultaneously).

---

### Full flow diagram

```
POST /graphql  ──►  get_context()
                        │  validates JWT
                        │  creates DataLoaders
                        │  stores session_factory
                        ▼
               strawberry.Schema  ──►  Query.films(filter, page, ...)
                                            │
                                            │  opens AsyncSession
                                            │  builds SELECT ... WHERE ...
                                            │  runs COUNT + SELECT
                                            ▼
                                       FilmConnection
                                        ├── items: [FilmType, ...]
                                        │       └── language  ──►  DataLoader._load_languages()
                                        │                              └── SELECT … IN (ids)
                                        │       └── actors    ──►  DataLoader._load_actors_by_film_id()
                                        │                              └── SELECT … IN (film_ids)
                                        └── page_info: PageInfo
```

---

### Strawberry keyword reference

| Decorator | Used on | Purpose |
|---|---|---|
| `@strawberry.type` | Class | Defines a **response** object (what the client can query) |
| `@strawberry.input` | Class | Defines an **argument** object (what the client can send) |
| `@strawberry.field` | Method | Marks a method as a GraphQL field with a custom resolver |
| `@strawberry.enum` | Enum class | Exposes a Python enum as a GraphQL enum |
| `strawberry.lazy(…)` | Type annotation | Defers type import to break circular imports |
| `Info` | Parameter type | Framework-injected object giving access to `context` |
