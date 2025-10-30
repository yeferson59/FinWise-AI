import app.tesseract_config  # noqa: F401
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.v1.router import router
from app.config import get_settings
from app.db.base import create_db_and_tables
from app.dependencies import init_categories
from fastapi.middleware.cors import CORSMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_db_and_tables()
    init_categories()
    yield


app = FastAPI(lifespan=lifespan)

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router=router, prefix=settings.prefix_api)
