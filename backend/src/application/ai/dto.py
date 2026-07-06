"""DTOs for the AI Chat Assistant."""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ChatMessage(BaseModel):
    """A single message in the conversation history."""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ToolDefinition(BaseModel):
    """Schema for a tool the AI can call."""
    name: str
    description: str
    parameters: dict  # JSON Schema for the parameters


class ToolCall(BaseModel):
    """A tool call made by the AI."""
    id: str
    name: str
    arguments: dict


class ToolResult(BaseModel):
    """Result of executing a tool."""
    call_id: str
    name: str
    result: str


class AskRequest(BaseModel):
    """Request to the AI chat assistant."""
    message: str = Field(..., min_length=1, max_length=10000)
    model: str = Field(default="gpt-4o")
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    stream: bool = Field(default=True)


class ModelInfo(BaseModel):
    """Info about an available model."""
    id: str
    name: str
    provider: str
    description: str
    available: bool


class SourceInfo(BaseModel):
    """A reference to a research object cited by the AI."""
    id: str
    type: str  # experiment, notebook, artifact, etc.
    title: str


class AskResponse(BaseModel):
    """The streaming response from the AI chat.

    For SSE streaming, each token is sent as a separate event.
    This model represents the final complete message.
    """
    message: ChatMessage
    sources: list[SourceInfo] = Field(default_factory=list)
    tool_calls: list[ToolCall] = Field(default_factory=list)
    session_id: str
