from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.v1.router import router
from app.config import get_settings
from app.db.base import create_db_and_tables

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(router=router, prefix=settings.prefix_api)
