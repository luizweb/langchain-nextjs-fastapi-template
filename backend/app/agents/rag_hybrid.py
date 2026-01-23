"""RAG Hybrid Agent with document grading using LangGraph StateGraph."""

from dataclasses import dataclass
from typing import Any, Literal

from langchain.messages import HumanMessage
from langchain.tools import ToolRuntime, tool
from langchain_core.runnables import Runnable
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.runtime import Runtime
from pydantic import BaseModel, Field

from app.services.file_content_service import FileContentService


@dataclass
class ProjectContext:
    """Contexto do projeto para a ferramenta RAG."""

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

    results = await FileContentService.search_similar(
        query=query,
        session=session,
        project_id=project_id
    )

    formatted_results = FileContentService.format_for_llm(results)
    return formatted_results


tools = [search_project_documents]


# --- PROMPTS ---
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

GRADE_PROMPT = """
You are a grader assessing relevance of a retrieved document.
Retrieved document: {context}
User question: {question}
If the document contains keywords or meaning related to the question,
grade it as relevant. Give a binary score 'yes' or 'no'.
"""

REWRITE_PROMPT = """
Look at the input and try to reason about the underlying
semantic intent / meaning.
Here is the initial question:
\n ------- \n
{question}
\n ------- \n
Formulate an improved question:
"""

GENERATE_PROMPT = """
You are an assistant for question-answering tasks.
Use the following pieces of retrieved context to answer the question.
If you don't know the answer, just say that you don't know.
Use three sentences maximum and keep the answer concise.
Question: {question} \n
Context: {context}
"""


class GradeDocuments(BaseModel):
    """Grade documents using a binary score for relevance check."""

    binary_score: str = Field(
        description="Relevance score: 'yes' if relevant, 'no' if not relevant"
    )


# --- FACTORY FUNCTION ---
def create_rag_hybrid_agent(
    llm: Runnable,
    checkpointer: AsyncPostgresSaver | None = None,
    grader_model: Runnable | None = None
):
    """Create a hybrid RAG agent with document grading capabilities.

    This agent implements an advanced RAG pattern with:
    - Query generation or direct response
    - Document retrieval via search tool
    - Document relevance grading
    - Question rewriting for irrelevant results
    - Final answer generation

    Args:
        llm: A LangChain Runnable LLM instance for main reasoning
        checkpointer: Optional AsyncPostgresSaver for conversation memory
        grader_model: Optional LLM for document grading (defaults to llm)

    Returns:
        A compiled StateGraph compatible with the chat endpoint
    """
    _grader_model = grader_model or llm

    def _get_last_human_question(messages) -> str:
        """Find the last human message (the actual question being asked)."""
        for msg in reversed(messages):
            if hasattr(msg, 'type') and msg.type == 'human':
                return msg.content
            elif isinstance(msg, dict) and msg.get('role') == 'user':
                return msg.get('content', '')
        # Fallback to first message
        return messages[0].content if messages else ''

    # --- Node functions (closure pattern) ---
    def generate_query_or_respond(
        state: MessagesState,
        runtime: Runtime[ProjectContext]
    ):
        """Generate a response or decide to use retrieval tool."""
        messages = state["messages"]
        if not messages or messages[0].type != "system":
            system_msg = {"role": "system", "content": SYSTEM_PROMPT}
            messages = [system_msg] + messages

        response = llm.bind_tools(tools).invoke(messages)
        return {"messages": [response]}

    def grade_documents(
        state: MessagesState,
        runtime: Runtime[ProjectContext]
    ) -> Literal["generate_answer", "rewrite_question"]:
        """Determine whether retrieved documents are relevant."""
        question = _get_last_human_question(state["messages"])
        context = state["messages"][-1].content

        prompt = GRADE_PROMPT.format(question=question, context=context)

        # Disable streaming for grader to prevent JSON leaking
        grader_chain = _grader_model.with_structured_output(GradeDocuments)
        response = grader_chain.invoke(
            [{"role": "user", "content": prompt}],
            config={"callbacks": []}
        )
        score = response.binary_score

        if score.lower() == "yes":
            return "generate_answer"
        return "rewrite_question"

    def rewrite_question(
        state: MessagesState,
        runtime: Runtime[ProjectContext]
    ):
        """Rewrite the original user question."""
        question = _get_last_human_question(state["messages"])
        prompt = REWRITE_PROMPT.format(question=question)
        response = llm.invoke([{"role": "user", "content": prompt}])
        return {"messages": [HumanMessage(content=response.content)]}

    def generate_answer(
        state: MessagesState,
        runtime: Runtime[ProjectContext]
    ):
        """Generate an answer based on retrieved context."""
        question = _get_last_human_question(state["messages"])
        context = state["messages"][-1].content
        prompt = GENERATE_PROMPT.format(question=question, context=context)
        response = llm.invoke([{"role": "user", "content": prompt}])
        return {"messages": [response]}

    # --- Build the graph ---
    workflow = StateGraph(MessagesState, context_schema=ProjectContext)

    workflow.add_node("generate_query_or_respond", generate_query_or_respond)
    workflow.add_node("retrieve", ToolNode(tools))
    workflow.add_node("rewrite_question", rewrite_question)
    workflow.add_node("generate_answer", generate_answer)

    workflow.add_edge(START, "generate_query_or_respond")

    workflow.add_conditional_edges(
        "generate_query_or_respond",
        tools_condition,
        {
            "tools": "retrieve",
            END: END,
        },
    )

    workflow.add_conditional_edges(
        "retrieve",
        grade_documents,
    )

    workflow.add_edge("generate_answer", END)
    workflow.add_edge("rewrite_question", "generate_query_or_respond")

    return workflow.compile(checkpointer=checkpointer)


# --- TEST ---
if __name__ == "__main__":

    import asyncio

    from app.database import get_session
    from app.services.llm import LLMFactory

    async def test_agent(project_id: int):
        """Test the hybrid RAG agent."""

        llm = LLMFactory().get_model("ollama", "gpt-oss:120b-cloud")
        grader = LLMFactory().get_model("ollama", "llama3.1")

        agent = create_rag_hybrid_agent(llm=llm, grader_model=grader)

        async for session in get_session():
            context = ProjectContext(
                project_id=project_id,
                session=session
            )

            print("\n\n=== TESTING HYBRID RAG AGENT ===\n")
            async for chunk in agent.astream(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": "O que disse Leao XIV sobre a IA?",
                        },
                    ]
                },
                context=context,
            ):
                for node, update in chunk.items():
                    print(f"*** Update from node: {node} ***")
                    update["messages"][-1].pretty_print()
                    print("\n")

    asyncio.run(test_agent(project_id=2))
