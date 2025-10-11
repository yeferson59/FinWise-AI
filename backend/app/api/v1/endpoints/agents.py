from fastapi import APIRouter
from app.core.llm import agent
from app.schemas.agent import ChatAgent

router = APIRouter()


@router.post("")
async def send_message(chatAgent: ChatAgent):
    response = await agent.run(chatAgent.message)
    return response.output
