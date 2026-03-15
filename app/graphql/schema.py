from __future__ import annotations

import strawberry

from app.graphql.resolvers.query import Query

schema = strawberry.Schema(query=Query)
