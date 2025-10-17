from app.core.llm import get_agent, AgentDeps, react_agent
from app.db.session import SessionDep

agent = get_agent()


async def chat_agent(message: str) -> str:
    response = await agent.run(message)
    return response.output


async def chat_react_agent(session: SessionDep, message: str) -> str:
    deps = AgentDeps(session=session)
    response = await react_agent.run(message, deps=deps)
    return response.output
