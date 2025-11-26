"""Agent client for making HTTP calls to agent endpoints."""

from __future__ import annotations

import httpx
import logging

from ..config import settings
from ..schemas import AgentRequest, AgentResponse

logger = logging.getLogger(__name__)

# Base URL for agent endpoints (internal)
AGENT_BASE_URL = f"http://localhost:{settings.backend_port}"


class AgentClient:
    """Client for calling agent endpoints via HTTP."""

    def __init__(self, base_url: str = AGENT_BASE_URL):
        self.base_url = base_url
        self.timeout = 60.0  # 60 second timeout for agent calls

    async def call_agent(self, agent_name: str, request: AgentRequest) -> AgentResponse:
        """
        Call an agent endpoint by name.
        
        Args:
            agent_name: Name of the agent (e.g., "rag-knowledge", "code-review-repo")
            request: Agent request payload
            
        Returns:
            AgentResponse from the agent endpoint
            
        Raises:
            httpx.HTTPError: If the HTTP request fails
        """
        url = f"{self.base_url}/api/agents/{agent_name}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json={
                        "prompt": request.prompt,
                        "history": [msg.model_dump() for msg in request.history],
                        "context": request.context,
                        "metadata": request.metadata,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return AgentResponse(**data)
        except httpx.HTTPError as e:
            logger.error(f"Error calling agent {agent_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling agent {agent_name}: {e}")
            raise


# Global agent client instance
_agent_client: AgentClient | None = None


def get_agent_client() -> AgentClient:
    """Get or create the global agent client instance."""
    global _agent_client
    if _agent_client is None:
        _agent_client = AgentClient()
    return _agent_client

