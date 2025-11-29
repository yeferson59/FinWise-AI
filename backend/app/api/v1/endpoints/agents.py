from fastapi import APIRouter

from app.db.session import SessionDep
from app.schemas.agent import ChatAgent
from app.services import agent

router = APIRouter()


@router.post("")
async def send_message(chatAgent: ChatAgent) -> str:
    """
    Send a message to the basic AI agent.

    This endpoint provides a simple chat interface with the AI agent
    without access to database tools.

    Parameters:
    - message: The message to send to the agent
    - user_id: The ID of the authenticated user (required for context)
    - temperature: Optional temperature parameter (0.0-1.0) to control response randomness
    - top_p: Optional top_p parameter (0.0-1.0) to control response diversity

    Returns:
    - The agent's response as a string
    """
    return await agent.chat_agent(
        chatAgent.message, chatAgent.temperature, chatAgent.top_p
    )


@router.post("/react")
async def send_message_agent_react(
    session: SessionDep,
    chatAgent: ChatAgent,
) -> str:
    """
    Send a message to the ReAct agent with database access.

    This endpoint provides an enhanced AI agent that can query the database
    and use various tools to provide informed responses about the user's
    transactions, categories, and financial analysis.

    SECURITY: The agent is scoped to only access data belonging to the
    authenticated user specified by user_id. It cannot access data from
    other users or sensitive system information.

    The agent follows the ReAct (Reasoning + Acting) pattern and can:
    - Retrieve and analyze the user's transactions
    - Calculate financial summaries and totals for the user
    - Provide spending analysis by category
    - Answer questions about the user's financial data

    Parameters:
    - message: The message to send to the agent
    - user_id: The ID of the authenticated user (required - scopes data access)
    - temperature: Optional temperature parameter (0.0-1.0) to control response randomness
    - top_p: Optional top_p parameter (0.0-1.0) to control response diversity

    Returns:
    - The agent's response as a string, potentially including data from database queries
    """
    return await agent.chat_react_agent(
        session=session,
        user_id=chatAgent.user_id,
        message=chatAgent.message,
        temperature=chatAgent.temperature,
        top_p=chatAgent.top_p,
    )
