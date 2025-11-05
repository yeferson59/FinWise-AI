from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import tesseract_config first to prevent SIGSEGV crashes
import app.tesseract_config  # noqa: F401

from app.api.v1.router import router
from app.config import get_settings
from app.db.base import create_db_and_tables
from app.dependencies import init_categories, init_sources

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_db_and_tables()
    init_categories()
    init_sources()
    yield


application = FastAPI(lifespan=lifespan)

origins = [
    "*",
]

application.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

application.include_router(router=router, prefix=settings.prefix_api)

# Keep app alias for backwards compatibility
app = application  # type: ignore[assignment]
