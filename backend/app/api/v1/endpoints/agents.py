from fastapi import APIRouter
from app.services import agent
from app.schemas.agent import ChatAgent

router = APIRouter()


@router.post("")
async def send_message(chatAgent: ChatAgent) -> str:
    return await agent.chat_agent(chatAgent.message)
