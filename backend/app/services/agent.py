from app.core.llm import agent, react_agent, AgentDeps
from app.db.session import SessionDep


async def chat_agent(message: str) -> str:
    response = await agent.run(message)
    return response.output


async def chat_react_agent(session: SessionDep, message: str) -> str:
    deps = AgentDeps(session=session)
    response = await react_agent.run(message, deps=deps)
    return response.output
