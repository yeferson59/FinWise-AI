from pydantic import BaseModel, Field


class ChatAgent(BaseModel):
    message: str = Field(description="The message to send to the agent")
