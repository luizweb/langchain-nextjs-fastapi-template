"""RAG Agent implementation with LangChain and LLM Factory support."""

from dataclasses import dataclass
from typing import Any

from langchain.agents import create_agent
from langchain.tools import ToolRuntime, tool
from langchain_core.runnables import Runnable
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.services.file_content_service import FileContentService


@dataclass
class ProjectContext:
    """Contexto do projeto para a ferramenta RAG."""

    project_id: int
    session: Any  # Using Any to avoid Pydantic serialization issues


@tool
async def search_project_documents(
    runtime: ToolRuntime[ProjectContext],
    query: str,
) -> str:
    """Ferramenta para pesquisar documentos do projeto.

    Args:
        runtime: Runtime context with project_id and session
        query: Search query

    Returns:
        Formatted search results
    """
    project_id = runtime.context.project_id
    session = runtime.context.session

    # Perform similarity search
    results = await FileContentService.search_similar(
        query=query,
        session=session,
        project_id=project_id
    )

    # Format results for LLM
    formatted_results = FileContentService.format_for_llm(results)
    return formatted_results


SYSTEM_PROMPT = """
Você é um assistente inteligente e prestativo.

Você tem acesso à ferramenta search_project_documents para consultar
documentos do projeto quando necessário.

IMPORTANTE:
- Se o usuário fizer perguntas sobre documentos específicos do projeto,
USE a ferramenta search_project_documents
- Se o usuário fizer perguntas gerais (matemática, conhecimento geral,
conversação), responda diretamente SEM usar ferramentas
- Seja claro, conciso e útil em suas respostas
- Mantenha o contexto da conversa para fornecer respostas coerentes
"""


def create_rag_agent(
    llm: Runnable,
    checkpointer: AsyncPostgresSaver | None = None
):
    """Create a RAG agent with the specified LLM and optional checkpointer.

    Args:
        llm: A LangChain Runnable LLM instance
        checkpointer: Optional AsyncPostgresSaver for conversation memory

    Returns:
        A configured RAG agent with memory support
    """
    return create_agent(
        model=llm,
        tools=[search_project_documents],
        context_schema=ProjectContext,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )
