"""
import sys
from pathlib import Path

# 1. Adiciona o diretório raiz ao path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 2. Carrega as variáveis de ambiente do arquivo .env
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

import nest_asyncio
nest_asyncio.apply()

"""
# import asyncio
from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Depends
from langchain.agents import create_agent
from langchain.tools import ToolRuntime, tool

# from langchain_core.messages import ToolMessage
from langchain_ollama import ChatOllama
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.services.file_content_service import FileContentService

Session = Annotated[AsyncSession, Depends(get_session)]

# Configuração do LLM
llm = ChatOllama(
    model="gpt-oss:120b-cloud",
    temperature=0,
)


@dataclass
class ProjectContext:
    """Contexto do projeto para a ferramenta RAG."""
    project_id: int
    session: Any  # ! Usando Any para evitar problemas de serialização Pydantic


@tool
async def search_project_documents(
    runtime: ToolRuntime[ProjectContext],
    query: str,
) -> str:
    """Ferramenta para pesquisar documentos"""
    project_id = runtime.context.project_id
    session = runtime.context.session

    # Aguarda a coroutine search_similar
    results = await FileContentService.search_similar(
        query=query,
        session=session,
        project_id=project_id
    )

    # Formata os resultados para o LLM
    formatted_results = FileContentService.format_for_llm(results)
    return formatted_results


SYSTEM_PROMPT = """
    Você é um especialista em buscar documentos.
    Use a ferramenta search_project_documents quando precisar!
"""

agent = create_agent(
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
