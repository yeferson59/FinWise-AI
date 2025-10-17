from app.core.llm import get_agent, get_react_agent, AgentDeps
from app.db.session import SessionDep

agent = get_agent()
react_agent = get_react_agent()


async def chat_agent(message: str) -> str:
    response = await agent.run(message)
    return response.output


async def chat_react_agent(session: SessionDep, message: str) -> str:
    deps = AgentDeps(session=session)
    response = await react_agent.run(message, deps=deps)
    return response.output
