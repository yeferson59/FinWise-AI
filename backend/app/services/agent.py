from app.core.llm import agent
from app.schemas.agent import ChatAgent


async def chat_agent(message: str) -> str:
    response = await agent.run(message)
    return response.output
