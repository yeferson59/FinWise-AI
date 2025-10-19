from app.core.agent import get_agent, AgentDeps, react_agent
from app.db.session import SessionDep


async def chat_agent(message: str) -> str:
    agent = get_agent()
    response = await agent.run(message)

    return response.output


async def chat_react_agent(session: SessionDep, message: str) -> str:
    deps = AgentDeps(session=session)
    response = await react_agent.run(message, deps=deps)

    return response.output
