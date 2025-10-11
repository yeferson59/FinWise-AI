from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.llm import agent

agents = APIRouter(
    prefix="/agents",
)


class ChatAgent(BaseModel):
    message: str = Field(description="The message to send to the agent")


@agents.post("", tags=["Agents"])
async def send_message(chatAgent: ChatAgent):
    response = await agent.run(chatAgent.message)
    return response
