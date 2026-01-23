"""RAG Agent implementation with LangChain and LLM Factory support."""

from dataclasses import dataclass
from typing import Any, Literal

from langchain.messages import HumanMessage
from langchain.tools import ToolRuntime, tool
from langchain_core.runnables import Runnable

# checkpointer
# * from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.runtime import Runtime
from pydantic import BaseModel, Field

from app.services.file_content_service import FileContentService
from app.services.llm import LLMFactory


@dataclass
class ProjectContext:
    """Contexto do projeto para a ferramenta RAG."""
    llm: Runnable
    project_id: int
    session: Any  # Using Any to avoid Pydantic serialization issues


# --- TOOLS ---
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


tools = [search_project_documents]

# --- SYSTEM PROMPT ---
SYSTEM_PROMPT = """
You are an intelligent and helpful assistant with access to project documents.

You have access to the search_project_documents tool to
query project documents when needed.

INSTRUCTIONS:
- When the user asks questions about specific project documents,
USE the search_project_documents tool
- For general questions (math, general knowledge, conversation),
respond directly WITHOUT using tools
- Be clear, concise, and helpful in your responses
- Maintain conversation context to provide coherent answers
- Always ground your answers in the retrieved documents when using the tool
- If the retrieved documents don't contain relevant information,
acknowledge this clearly
"""


# --- GENERATE QUERY (TOOL) OR RESPOND ---
def generate_query_or_respond(
        state: MessagesState,
        runtime: Runtime[ProjectContext]
    ):
    """Call the model to generate a response based on the current state. Given
    the question, it will decide to retrieve using the retriever tool,
    or simply respond to the user.
    """
    llm = runtime.context.llm
    messages = state["messages"]
    if not messages or messages[0].type != "system":
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    response = llm.bind_tools(tools).invoke(messages)
    return {"messages": [response]}


# --- GRADE DOCUMENTS ---
GRADE_PROMPT = """
You are a grader assessing relevance
of a retrieved document to a user question.
Here is the retrieved document: {context}
Here is the user question: {question}
If the document contains keyword(s) or semantic meaning related to the user
question, grade it as relevant.
Give a binary score 'yes' or 'no' score to indicate whether
the document is relevant to the question.
"""


class GradeDocuments(BaseModel):
    """Grade documents using a binary score for relevance check."""

    binary_score: str = Field(
        description="Relevance score: 'yes' if relevant, 'no' if not relevant"
    )


# ! Posso usar um modelo menor para a classificação de documentos (?)
grader_model = LLMFactory().get_model("ollama", "llama3.1")


def grade_documents(
    state: MessagesState,
) -> Literal["generate_answer", "rewrite_question"]:
    """Determine whether the retrieved documents
    are relevant to the question."""
    question = state["messages"][0].content
    context = state["messages"][-1].content

    prompt = GRADE_PROMPT.format(question=question, context=context)

    response = (
        grader_model.with_structured_output(GradeDocuments).invoke(
            [{"role": "user", "content": prompt}]
        )
    )
    score = response.binary_score

    if score.lower() == "yes":
        print("✅ Documents are RELEVANT → Generating answer")
        return "generate_answer"
    else:
        print("❌ Documents are NOT RELEVANT → Rewriting question")
        return "rewrite_question"


# --- REWRITE QUESTION ---

REWRITE_PROMPT = """
Look at the input and try to reason about the underlying
semantic intent / meaning.
Here is the initial question:
\n ------- \n
{question}
\n ------- \n
Formulate an improved question:
"""


def rewrite_question(
        state: MessagesState,
        runtime: Runtime[ProjectContext]
    ):
    """Rewrite the original user question."""
    llm = runtime.context.llm
    messages = state["messages"]
    question = messages[0].content
    prompt = REWRITE_PROMPT.format(question=question)
    response = llm.invoke([{"role": "user", "content": prompt}])
    return {"messages": [HumanMessage(content=response.content)]}


# --- GENERATE AN ANSWER ---

GENERATE_PROMPT = """
You are an assistant for question-answering tasks.
Use the following pieces of retrieved context to answer the question.
If you don't know the answer, just say that you don't know.
Use three sentences maximum and keep the answer concise.
Question: {question} \n
Context: {context}
"""


def generate_answer(
        state: MessagesState,
        runtime: Runtime[ProjectContext]
    ):
    """Generate an answer."""
    llm = runtime.context.llm
    question = state["messages"][0].content
    context = state["messages"][-1].content
    prompt = GENERATE_PROMPT.format(question=question, context=context)
    response = llm.invoke([{"role": "user", "content": prompt}])
    return {"messages": [response]}

# -------------------------------------------------------


workflow = StateGraph(MessagesState)

# Define the nodes we will cycle between
workflow.add_node("generate_query_or_respond", generate_query_or_respond)
workflow.add_node("retrieve", ToolNode(tools))
workflow.add_node("rewrite_question", rewrite_question)
workflow.add_node("generate_answer", generate_answer)

workflow.add_edge(START, "generate_query_or_respond")

# Decide whether to retrieve
workflow.add_conditional_edges(
    "generate_query_or_respond",
    # Assess LLM decision (call `retriever_tool` tool or respond to the user)
    tools_condition,
    {
        # Translate the condition outputs to nodes in our graph
        "tools": "retrieve",
        END: END,
    },
)

# Edges taken after the `action` node is called.
workflow.add_conditional_edges(
    "retrieve",
    # Assess agent decision
    grade_documents,
)
workflow.add_edge("generate_answer", END)
workflow.add_edge("rewrite_question", "generate_query_or_respond")

# Compile
graph = workflow.compile()


# --------------------
# --- Teste de uso ---
# --------------------
if __name__ == "__main__":

    import asyncio

    # from langchain_core.messages import convert_to_messages
    from app.database import get_session
    from app.services.llm import LLMFactory

    # # Salva visualização do grafo
    # try:
    #     png_data = graph.get_graph().draw_mermaid_png()
    #     with open("rag_graph.png", "wb") as f:
    #         f.write(png_data)
    #     print("Grafo salvo: rag_graph.png")
    # except Exception:
    #     print("Erro")

    async def test_agent(project_id: int):
        """Teste direto do agente."""

        # ###################################################################
        # Para testar os nodes separadamente,
        # tem que alterar as funções para receber 'llm' como Runnable
        # e não como contexto 'runtime'. Exemplo:
        # def generate_query_or_respond(llm: Runnable, state: MessagesState):
        # ###################################################################

        # Cria o LLM
        llm = LLMFactory().get_model("ollama", "gpt-oss:120b-cloud")

        # Pega uma sessão do banco
        async for session in get_session():
            # # --- generate_query_or_respond ---
            # # Decide se chama a ferramenta ou responde diretamente
            # input = {
            #     "messages": [
            #         {"role": "user",
            #         "content": """
            #             O que disse Leão XIV sobre o uso da IA?
            #             utilize a ferramenta!"""
            #         }
            #     ]
            # }
            # generate_query_or_respond(llm, input)["messages"][-1].pretty_print()  # noqa: E501

            # # --- grade_documents --- deve responder 'no' ---
            # input = {
            # "messages": convert_to_messages(
            #     [
            #         {
            #             "role": "user",
            #             "content": """
            #                 What does Lilian Weng say
            #                 about types of reward hacking?
            #             """,
            #         },
            #         {
            #             "role": "assistant",
            #             "content": "",
            #             "tool_calls": [
            #                 {
            #                     "id": "1",
            #                     "name": "search_project_documents",
            #                     "args": {"query": "types of reward hacking"},
            #                 }
            #             ],
            #         },
            #         {"role": "tool", "content": "meow", "tool_call_id": "1"},
            #         ]
            #     )
            # }
            # grade_documents(input)

            # # --- grade_documents --- deve responder 'yes' ---
            # input = {
            #     "messages": convert_to_messages(
            #         [
            #             {
            #                 "role": "user",
            #                 "content": """
            #                     What does Lilian Weng say
            #                     about types of reward hacking?
            #                 """,
            #             },
            #             {
            #                 "role": "assistant",
            #                 "content": "",
            #                 "tool_calls": [
            #                     {
            #                         "id": "2",
            #                         "name": "search_project_documents",
            #                         "args": {
            #                               "query": "types of reward hacking"
            #                               },
            #                     }
            #                 ],
            #             },
            #             {
            #                 "role": "tool",
            #                 "content": """
            #                     reward hacking can be categorized
            #                     into two types: environment or
            #                     goal misspecification,
            #                     and reward tampering""",
            #                 "tool_call_id": "2",
            #             },
            #         ]
            #     )
            # }
            # grade_documents(input)

            # # --- rewrite question ---
            # input = {
            #     "messages": convert_to_messages(
            #         [
            #             {
            #                 "role": "user",
            #                 "content": """
            #                     O que disse Leão XIV sobre o uso da IA?
            #                 """,
            #             },
            #         ]
            #     )
            # }

            # response = rewrite_question(llm, input)
            # print(response["messages"][-1].content)

            # # --- generate_answer ---
            # response = generate_answer(llm, input)
            # response["messages"][-1].pretty_print()

            # --- Test complete graph streaming ---
            print("\n\n=== TESTING COMPLETE GRAPH ===\n")
            async for chunk in graph.astream(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content":
                                "O que disse Leão XIV sobre o uso da IA?",
                        },
                    ]
                },
                context=ProjectContext(
                            llm=llm,
                            project_id=project_id,
                            session=session
                        )
            ):
                for node, update in chunk.items():
                    print("*** Update from node ***", node)
                    update["messages"][-1].pretty_print()
                    print("\n\n")

    response = asyncio.run(
        test_agent(project_id=2)
    )
