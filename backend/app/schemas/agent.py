from pydantic import BaseModel, Field


class ChatAgent(BaseModel):
    message: str = Field(description="The message to send to the agent")
    temperature: float | None = Field(
        default=None,
        description="Controls randomness in responses. Lower values (e.g., 0.2) make output more focused and deterministic, higher values (e.g., 0.8) make it more creative and varied. Range: 0.0 to 1.0",
        ge=0.0,
        le=1.0,
    )
    top_p: float | None = Field(
        default=None,
        description="Controls diversity via nucleus sampling. Lower values (e.g., 0.3) focus on high-probability tokens, higher values (e.g., 0.9) allow more diversity. Range: 0.0 to 1.0",
        ge=0.0,
        le=1.0,
    )
