from fastapi import APIRouter
from app.db.session import SessionDep
from app.services import agent
from app.schemas.agent import ChatAgent

router = APIRouter()


@router.post("")
async def send_message(chatAgent: ChatAgent) -> str:
    return await agent.chat_agent(chatAgent.message)


@router.post("/react")
async def send_message_agent_react(chatAgent: ChatAgent, session: SessionDep):
    return await agent.chat_react_agent(session, chatAgent.message)
