from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import async_sessionmaker
from strawberry.fastapi import BaseContext

if TYPE_CHECKING:
    from app.graphql.dataloaders import DataLoaders


class GraphQLContext(BaseContext):
    session_factory: async_sessionmaker
    current_user: dict
    loaders: "DataLoaders"

    def __init__(
        self,
        session_factory: async_sessionmaker,
        current_user: dict,
        loaders: "DataLoaders",
    ) -> None:
        super().__init__()
        self.session_factory = session_factory
        self.current_user = current_user
        self.loaders = loaders
