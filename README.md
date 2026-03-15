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
