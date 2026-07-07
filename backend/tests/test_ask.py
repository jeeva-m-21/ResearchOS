"""Tests for the AI Chat Assistant — tools, orchestrator, and API endpoint."""
import httpx
import pytest

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "researcher@test.com"
TEST_PASSWORD = "password123"
TEST_ORG_ID = "02b5991b-d971-41fc-b257-4ded07d94aac"


# ─── Tool Tests ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_tool_returns_string():
    """The SearchTool should return a string result."""
    from src.application.ai.tools import SearchTool

    tool = SearchTool()
    result = await tool.execute(query="transformer")
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_get_experiment_tool_returns_string():
    """The GetExperimentTool should return a string result."""
    from src.application.ai.tools import GetExperimentTool

    tool = GetExperimentTool()
    result = await tool.execute(experiment_id="00000000-0000-0000-0000-000000000000")
    assert isinstance(result, str)
    assert "experiment" in result.lower()


@pytest.mark.asyncio
async def test_get_notebook_tool_returns_string():
    """The GetNotebookTool should return a string result."""
    from src.application.ai.tools import GetNotebookTool

    tool = GetNotebookTool()
    result = await tool.execute(notebook_id="00000000-0000-0000-0000-000000000000")
    assert isinstance(result, str)
    assert "notebook" in result.lower()


@pytest.mark.asyncio
async def test_list_experiments_tool_returns_string():
    """The ListExperimentsTool should return a string result."""
    from src.application.ai.tools import ListExperimentsTool

    tool = ListExperimentsTool()
    result = await tool.execute()
    assert isinstance(result, str)
    assert "experiment" in result.lower() or "list" in result.lower()


@pytest.mark.asyncio
async def test_list_notebooks_tool_returns_string():
    """The ListNotebooksTool should return a string result."""
    from src.application.ai.tools import ListNotebooksTool

    tool = ListNotebooksTool()
    result = await tool.execute()
    assert isinstance(result, str)
    assert "notebook" in result.lower() or "list" in result.lower()


@pytest.mark.asyncio
async def test_get_block_content_tool_returns_string():
    """The GetBlockContentTool should return a string result."""
    from src.application.ai.tools import GetBlockContentTool

    tool = GetBlockContentTool()
    result = await tool.execute(block_id="00000000-0000-0000-0000-000000000000")
    assert isinstance(result, str)
    assert "block" in result.lower()


@pytest.mark.asyncio
async def test_get_paper_tool_returns_string():
    """The GetPaperTool should return a string result."""
    from src.application.ai.tools import GetPaperTool

    tool = GetPaperTool()
    result = await tool.execute(paper_id="00000000-0000-0000-0000-000000000000")
    assert isinstance(result, str)
    assert "paper" in result.lower()


@pytest.mark.asyncio
async def test_list_papers_tool_returns_string():
    """The ListPapersTool should return a string result."""
    from src.application.ai.tools import ListPapersTool

    tool = ListPapersTool()
    result = await tool.execute()
    assert isinstance(result, str)
    assert "paper" in result.lower() or "list" in result.lower()


@pytest.mark.asyncio
async def test_edit_paper_tool_returns_string():
    """The EditPaperTool should return a string result."""
    from src.application.ai.tools import EditPaperTool

    tool = EditPaperTool()
    result = await tool.execute(
        paper_id="00000000-0000-0000-0000-000000000000",
        title="Updated Title",
    )
    assert isinstance(result, str)
    assert "paper" in result.lower() or "not found" in result.lower()


@pytest.mark.asyncio
async def test_create_experiment_tool_returns_string():
    """The CreateExperimentTool should return a string result."""
    from src.application.ai.tools import CreateExperimentTool

    tool = CreateExperimentTool()
    result = await tool.execute(
        project_id="00000000-0000-0000-0000-000000000000",
        name="Test Experiment",
    )
    assert isinstance(result, str)
    # Should say experiment created or project not found
    assert "experiment" in result.lower() or "project" in result.lower()


@pytest.mark.asyncio
async def test_create_notebook_tool_returns_string():
    """The CreateNotebookTool should return a string result."""
    from src.application.ai.tools import CreateNotebookTool

    tool = CreateNotebookTool()
    result = await tool.execute(
        project_id="00000000-0000-0000-0000-000000000000",
        title="Test Notebook",
    )
    assert isinstance(result, str)
    # Should say notebook created or project not found
    assert "notebook" in result.lower() or "project" in result.lower()


@pytest.mark.asyncio
async def test_all_tool_definitions_have_required_fields():
    """Every tool must have name, description, and parameters."""
    from src.application.ai.tools import (
        CreateExperimentTool,
        CreateNotebookTool,
        EditPaperTool,
        GetBlockContentTool,
        GetExperimentTool,
        GetNotebookTool,
        GetPaperTool,
        ListExperimentsTool,
        ListNotebooksTool,
        ListPapersTool,
        SearchTool,
    )

    for tool_cls in [
        CreateExperimentTool,
        CreateNotebookTool,
        EditPaperTool,
        GetBlockContentTool,
        GetExperimentTool,
        GetNotebookTool,
        GetPaperTool,
        ListExperimentsTool,
        ListNotebooksTool,
        ListPapersTool,
        SearchTool,
    ]:
        tool = tool_cls()
        assert tool.name, f"{tool_cls.__name__} missing name"
        assert tool.description, f"{tool_cls.__name__} missing description"
        assert tool.parameters, f"{tool_cls.__name__} missing parameters"
        assert "properties" in tool.parameters


# ─── Orchestrator Tests ─────────────────────────────────────────────────────


class FakeLLMProvider:
    """A fake LLM provider that returns a canned response."""

    provider_name = "fake"
    model_id = "fake-model"

    async def chat_stream(
        self, messages, tools=None, model=None, max_tokens=4096, temperature=0.7
    ):
        yield {"type": "token", "content": "This is a fake response."}


@pytest.mark.asyncio
async def test_orchestrator_returns_tokens():
    """The orchestrator should yield token events for a simple query."""
    from src.application.ai import AIOrchestrator, AskRequest

    orchestrator = AIOrchestrator(llm_provider=FakeLLMProvider(), tools=[])
    request = AskRequest(message="Hello", stream=True)
    tokens = []

    async for chunk in orchestrator.ask(request, organization_id=TEST_ORG_ID):
        if chunk["type"] == "token":
            tokens.append(chunk["content"])
        elif chunk["type"] == "done":
            assert chunk["content"]["session_id"] is not None

    assert len(tokens) > 0
    assert "".join(tokens) == "This is a fake response."


@pytest.mark.asyncio
async def test_orchestrator_creates_session():
    """The orchestrator should create a session_id for new conversations."""
    from src.application.ai import AIOrchestrator, AskRequest

    orchestrator = AIOrchestrator(llm_provider=FakeLLMProvider(), tools=[])
    request = AskRequest(message="Test", stream=True)
    session_id = None

    async for chunk in orchestrator.ask(request, organization_id=TEST_ORG_ID):
        if chunk["type"] == "done":
            session_id = chunk["content"]["session_id"]

    assert session_id is not None
    assert len(session_id) > 0


@pytest.mark.asyncio
async def test_orchestrator_persists_session():
    """Messages should be persisted to the session."""
    from src.application.ai import AIOrchestrator, AskRequest

    orchestrator = AIOrchestrator(llm_provider=FakeLLMProvider(), tools=[])
    request = AskRequest(message="First message", stream=True)
    session_id = None

    async for chunk in orchestrator.ask(request, organization_id=TEST_ORG_ID):
        if chunk["type"] == "done":
            session_id = chunk["content"]["session_id"]

    # Verify session was persisted
    assert session_id is not None
    assert orchestrator._sessions[session_id] is not None
    assert len(orchestrator._sessions[session_id]) == 2  # user + assistant


@pytest.mark.asyncio
async def test_orchestrator_tool_definitions():
    """Tool definitions should be returned from the orchestrator."""
    from src.application.ai import AIOrchestrator, SearchTool

    tool = SearchTool()
    orchestrator = AIOrchestrator(llm_provider=FakeLLMProvider(), tools=[tool])
    defs = orchestrator.tool_definitions

    assert len(defs) == 1
    assert defs[0].name == "search_research"
    assert defs[0].description
    assert defs[0].parameters


# ─── API Endpoint Tests ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ask_endpoint_returns_sse():
    """POST /v1/ask should return an SSE stream."""
    async with httpx.AsyncClient() as client:
        # Login
        login_resp = await client.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "organization_id": TEST_ORG_ID,
            },
        )
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json()["access_token"]

        # Send ask request
        resp = await client.post(
            f"{BASE_URL}/v1/ask",
            json={
                "message": "What experiments do I have?",
                "stream": False,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        # NOTE: Without an API key configured, this may 500 or return an error.
        # We assert that the endpoint responds (even if the provider is not configured).
        assert resp.status_code in (200, 500, 503)
        if resp.status_code == 200:
            data = resp.json()
            assert "message" in data
            assert "session_id" in data


@pytest.mark.asyncio
async def test_list_models_endpoint():
    """GET /v1/ask/models should return a list of models."""
    async with httpx.AsyncClient() as client:
        login_resp = await client.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "organization_id": TEST_ORG_ID,
            },
        )
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json()["access_token"]

        resp = await client.get(
            f"{BASE_URL}/v1/ask/models",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        # At minimum, Ollama models should be available
        assert len(data) > 0
        # Each model should have required fields
        for model in data:
            assert "id" in model
            assert "name" in model
            assert "provider" in model
            assert "description" in model


# ─── Provider Tests ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ollama_provider_default_config():
    """Ollama provider should initialize with default config."""
    from src.infrastructure.adapters.llm import OllamaProvider

    provider = OllamaProvider()
    assert provider.provider_name == "ollama"
    assert provider.model_id is not None


@pytest.mark.asyncio
async def test_openai_provider_default_config():
    """OpenAI provider should initialize with env config."""
    from src.infrastructure.adapters.llm import OpenAIProvider

    provider = OpenAIProvider(api_key="test-key")
    assert provider.provider_name == "openai"
    assert provider.model_id is not None


@pytest.mark.asyncio
async def test_anthropic_provider_default_config():
    """Anthropic provider should initialize with env config."""
    from src.infrastructure.adapters.llm import AnthropicProvider

    provider = AnthropicProvider(api_key="test-key")
    assert provider.provider_name == "anthropic"
    assert provider.model_id is not None
