from fastapi import APIRouter

users = APIRouter(
    prefix="/users",
)


@users.get("", tags=["users"])
async def read_users():
    return {"users": ["Alice", "Bob", "Charlie"]}
