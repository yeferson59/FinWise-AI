from typing import Any
from app.core.agent import get_agent, AgentDeps, react_agent
from app.db.session import SessionDep


async def chat_agent(
    message: str, temperature: float | None = None, top_p: float | None = None
) -> str:
    agent = get_agent()

    # Build model settings, using provided values or falling back to defaults
    model_settings: dict[str, Any] = {}
    if temperature is not None:
        model_settings["temperature"] = temperature
    if top_p is not None:
        model_settings["top_p"] = top_p

    if model_settings:
        response = await agent.run(message, model_settings=model_settings)  # type: ignore[call-overload]
    else:
        response = await agent.run(message)

    return response.output


async def chat_react_agent(
    session: SessionDep,
    message: str,
    temperature: float | None = None,
    top_p: float | None = None,
) -> str:
    deps = AgentDeps(session=session)

    # Build model settings, using provided values or falling back to defaults
    model_settings: dict[str, Any] = {}
    if temperature is not None:
        model_settings["temperature"] = temperature
    if top_p is not None:
        model_settings["top_p"] = top_p

    if model_settings:
        response = await react_agent.run(  # type: ignore[call-overload]
            message, deps=deps, model_settings=model_settings
        )
    else:
        response = await react_agent.run(message, deps=deps)

    return response.output
