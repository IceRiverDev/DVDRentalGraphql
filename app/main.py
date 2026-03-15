from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy import text
from strawberry.fastapi import GraphQLRouter

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal, engine
from app.core.security import get_current_user_from_request
from app.graphql.context import GraphQLContext
from app.graphql.dataloaders import DataLoaders
from app.graphql.schema import schema


async def get_context(request: Request) -> GraphQLContext:
    # GET requests load the GraphiQL UI — skip auth
    if request.method == "GET":
        loaders = DataLoaders()
        return GraphQLContext(session_factory=AsyncSessionLocal, current_user={}, loaders=loaders)
    current_user = await get_current_user_from_request(request)
    loaders = DataLoaders()
    return GraphQLContext(session_factory=AsyncSessionLocal, current_user=current_user, loaders=loaders)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    graphql_app = GraphQLRouter(schema, context_getter=get_context)
    app.include_router(graphql_app, prefix="/graphql")

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "DVDRental GraphQL API"}

    return app


app = create_app()
