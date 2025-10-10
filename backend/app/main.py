from fastapi import FastAPI
from app.routers.users import users

app = FastAPI()
prefix = "/api/v1"

app.include_router(prefix=prefix, router=users)


@app.get("/")
def read_root():
    return {"Hello": "World"}
