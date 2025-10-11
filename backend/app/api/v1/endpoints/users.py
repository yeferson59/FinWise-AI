from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def read_users():
    return {"users": ["Alice", "Bob", "Charlie"]}
