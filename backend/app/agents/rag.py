"""RAG Agent implementation with LangChain and LLM Factory support."""

from dataclasses import dataclass
from typing import Any

from langchain.agents import create_agent
from langchain.tools import ToolRuntime, tool
from langchain_core.runnables import Runnable

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
"""


def create_rag_agent(llm: Runnable):
    """Create a RAG agent with the specified LLM.

    Args:
        llm: A LangChain Runnable LLM instance

    Returns:
        A configured RAG agent
    """
    return create_agent(
        model=llm,
        tools=[search_project_documents],
        context_schema=ProjectContext,
        system_prompt=SYSTEM_PROMPT
    )


# --- Teste de uso ---

# --- INVOKE ---
# async def test_agent():
#     """Função de teste assíncrona para o agente"""
#     try:
#         # Cria uma sessão real para teste
#         async for session in get_session():
#             result = await agent.ainvoke(
#                 {"messages": [
#                     {
#                         "role": "user",
#                         "content": "O que disse Leão XIV sobre o uso da IA?"
#                     }
#                 ]},
#                 context=ProjectContext(
#                     project_id=4,
#                     session=session
#                 )
#             )
#             return result
#     except Exception as e:
#         return f"Erro ao executar agente: {str(e)}"

# --- STREAM - UPDATES ---
# async def test_agent_stream_update():
#     """Função de teste assíncrona com streaming"""
#     try:
#         async for session in get_session():

#             query = (
#                 # "O que disse Leão XIV sobre o uso da IA?"
#                 "OI, TUDO BEM?"
#             )

#             async for event in agent.astream(
#                 {
#                     "messages": [
#                         {"role": "user", "content": query}
#                     ]
#                 },
#                 context=ProjectContext(
#                     project_id=4,
#                     session=session
#                 ),
#                 stream_mode="updates",
#             ):
#                 for step, data in event.items():
#                     print(f"step: {step}")  # model or tool
#                     print(f"content: {data['messages'][-1].content_blocks}")

#                     content_blocks = data['messages'][-1].content_blocks

#                     # print(f"content type: {content_blocks[0]["type"]}")

#                     if (
#                         step == "model"
#                     ) and (
#                         content_blocks[0]["type"] == "tool_call"
#                     ):
#                         print(f"TOOL_CALL:{content_blocks[0]["name"]}")

#                     # if (
#                     #     step == "tools"
#                     # ) and (
#                     #     content_blocks[0]["type"] == "text"
#                     # ):
#                     #     print(f"RESULT TOOLS:{content_blocks[0]["text"]}")

#                     if (
#                         step == "model"
#                     ) and (
#                         content_blocks[0]["type"] == "text"
#                     ):
#                         print(f"RESPOSTA: {content_blocks[0]["text"]}")

#                 # Cada `event` contém o estado atual do agente
#                 # last_message = event["messages"][-1]
#                 # last_message.pretty_print()

#             return "Streaming finalizado"

#     except Exception as e:
#         return f"Erro ao executar agente: {str(e)}"


# --- STREAM - MESSAGES (TOKENS) ---
# async def test_agent_stream_messages():
#     """Função de teste assíncrona com streaming"""
#     try:
#         tool_results = {}  # 👈 aqui você guarda os resultados
#         # total_prompt = 0
#         # total_completion = 0

#         async for session in get_session():

#             query = (
#                 # "O que disse Leão XIV sobre o uso da IA?"
#                 "Olá, tudo bem?"
#             )

#             async for token, metadata in agent.astream(
#                 {
#                     "messages": [
#                         {"role": "user", "content": query}
#                     ]
#                 },
#                 context=ProjectContext(
#                     project_id=4,
#                     session=session
#                 ),
#                 stream_mode="messages",
#             ):
#                 # print(f"TOKEN: {token}")
#                 # print(f"METADATA: {metadata}")
#                 # print(f"NODE: {metadata['langgraph_node']}")
#                 # print(f"CONTENT: {token.content_blocks}")
#                 # print("\n")
#                 # print("=====================================")
#                 # print("\n")

#                 # # 👇 DETECÇÃO DE TOOL CALL
#                 # if getattr(token, "tool_calls", None):
#                 #     for tool_call in token.tool_calls:
#                 #         print(f"[tool_call] {tool_call['name']}")

#                 # # resto do streaming normal
#                 # if token.content:
#                 #     print(token.content)

#                 # 1️⃣ Tool call (modelo pedindo ferramenta)
#                 if getattr(token, "tool_calls", None):
#                     for tool_call in token.tool_calls:
#                         print(f"[tool_call] {tool_call['name']}")

#                 # 2️⃣ Tool result (retorno da ferramenta)
#                 elif isinstance(token, ToolMessage):
#                     tool_results[token.tool_call_id] = {
#                         "tool_name": token.name,
#                         "content": token.content,
#                     }
#                     # ❌ não printa
#                     continue

#                 # 3️⃣ Texto normal do modelo
#                 elif token.content:
#                     print(token.content, end="", flush=True)

#                 # usage = token.response_metadata.get("token_usage")
#                 # if usage:
#                 #     total_prompt += usage.get("prompt_tokens", 0)
#                 #     total_completion += usage.get("completion_tokens", 0)

#         # Tokens
#         # print("Prompt:", total_prompt)
#         # print("Completion:", total_completion)
#         # print("Total:", total_prompt + total_completion)

#         # depois você pode usar isso
#         print("\n\n[DEBUG] Tool results armazenados:")
#         print(tool_results)

#         return "Streaming finalizado"

#     except Exception as e:
#         return f"Erro ao executar agente: {str(e)}"


# # Para execução direta (apenas para teste)
# if __name__ == "__main__":
#     # result = asyncio.run(test_agent())
#     asyncio.run(test_agent_stream_update())
#     asyncio.run(test_agent_stream_messages())
