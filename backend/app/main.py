from fastapi import FastAPI
from app.api.v1.router import router
from app.config import get_settings

settings = get_settings()

app = FastAPI()
prefix = "/api/v1"

app.include_router(router=router, prefix=prefix)


@app.get("/")
def read_root():
    return {"Hello": "World"}
