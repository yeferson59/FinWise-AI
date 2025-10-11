from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.core.llm import agent

router = APIRouter()


class ChatAgent(BaseModel):
    message: str = Field(description="The message to send to the agent")


@router.post("")
async def send_message(chatAgent: ChatAgent):
    response = await agent.run(chatAgent.message)
    return response.output
