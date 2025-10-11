from fastapi import FastAPI
from app.routers.users import users
from app.routers.agents import agents
from app.config import get_settings

settings = get_settings()

app = FastAPI()
prefix = "/api/v1"

app.include_router(prefix=prefix, router=users)
app.include_router(prefix=prefix, router=agents)


@app.get("/")
def read_root():
    return {"Hello": "World"}
