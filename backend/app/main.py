from fastapi import FastAPI
from app.routers.users import users

app = FastAPI()

app.include_router(prefix="/api/v1", router=users)


@app.get("/")
def read_root():
    return {"Hello": "World"}
