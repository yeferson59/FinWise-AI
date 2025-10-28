from fastapi import APIRouter
from app.db.session import SessionDep
from app.services import agent
from app.schemas.agent import ChatAgent

router = APIRouter()


@router.post("")
async def send_message(chatAgent: ChatAgent) -> str:
    """
    Send a message to the basic AI agent.

    This endpoint provides a simple chat interface with the AI agent
    without access to database tools.

    Parameters:
    - message: The message to send to the agent
    - temperature: Optional temperature parameter (0.0-1.0) to control response randomness
    - top_p: Optional top_p parameter (0.0-1.0) to control response diversity

    Returns:
    - The agent's response as a string
    """
    return await agent.chat_agent(
        chatAgent.message, chatAgent.temperature, chatAgent.top_p
    )


@router.post("/react")
async def send_message_agent_react(session: SessionDep, chatAgent: ChatAgent) -> str:
    """
    Send a message to the ReAct agent with database access.

    This endpoint provides an enhanced AI agent that can query the database
    and use various tools to provide informed responses about users,
    transactions, categories, and financial analysis.

    The agent follows the ReAct (Reasoning + Acting) pattern and can:
    - Query user information and statistics
    - Retrieve and analyze transactions
    - Calculate financial summaries and totals
    - Provide spending analysis by category
    - Answer questions about financial data

    Parameters:
    - message: The message to send to the agent
    - temperature: Optional temperature parameter (0.0-1.0) to control response randomness
    - top_p: Optional top_p parameter (0.0-1.0) to control response diversity

    Returns:
    - The agent's response as a string, potentially including data from database queries
    """
    return await agent.chat_react_agent(
        session, chatAgent.message, chatAgent.temperature, chatAgent.top_p
    )
