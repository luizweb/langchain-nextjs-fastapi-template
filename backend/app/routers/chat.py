# import logging
import json
import tempfile
from collections import defaultdict
from typing import Annotated
from urllib.parse import unquote

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse  # texto incremental
from langchain_core.messages import ToolMessage
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.rag_hybrid import ProjectContext, create_rag_hybrid_agent
from app.database import get_checkpointer, get_session
from app.models import Conversation, FileContent, Project, User
from app.schemas import (
    ChatRequest,
    ConversationCreate,
    ConversationList,
    ConversationPublic,
    ConversationUpdate,
    FileContentPublic,
    FilesList,
    LLMProviderInfo,
    LLMProvidersResponse,
)
from app.security import get_current_user
from app.services import (
    ConversationService,
    FileContentService,
    PDFProcessingService,
)
from app.services.llm import LLMFactory
from app.settings import Settings

# Configure logging para debug
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

router = APIRouter()

CurrentUser = Annotated[User, Depends(get_current_user)]
Session = Annotated[AsyncSession, Depends(get_session)]
UploadedPDF = Annotated[
    UploadFile,
    File(
        ...,
        description="PDF file to upload",
    ),
]


@router.post("/upload/{project_id}")
async def upload_pdf_to_project(
    project_id: int,
    session: Session,
    current_user: CurrentUser,
    uploaded_file: UploadedPDF,
):
    """
    Upload and process a PDF file.

    The PDF is processed in memory and not stored permanently.
    Chunks are extracted and stored in the database with embeddings.
    """
    # Validate PDF
    if uploaded_file.content_type not in {
        "application/pdf",
        "application/x-pdf"
    }:
        raise HTTPException(status_code=400, detail="File must be a PDF")

    # Verify project ownership
    project = await session.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Read PDF into memory
    file_bytes = await uploaded_file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    # Process PDF using service
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(file_bytes)
            tmp.flush()

            # Service handles all processing
            processed_records = PDFProcessingService.process_pdf_file(
                pdf_path=tmp.name,
                filename=uploaded_file.filename,
                project_id=project_id,
            )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing PDF: {exc}"
        )

    if not processed_records:
        raise HTTPException(
            status_code=400,
            detail="No content extracted from PDF"
        )

    # Save to database using service
    chunks_inserted = await FileContentService.bulk_create(
        records=processed_records,
        session=session,
    )

    return {
        "message": "PDF processed successfully",
        "chunks_inserted": chunks_inserted,
    }


@router.get("/files/{project_id}")
async def get_files_from_project(
    project_id: int,
    session: Session,
    current_user: CurrentUser,
):
    """List all files uploaded to a specific project.

    Args:
        project_id: The project ID
        session: Database session
        current_user: Authenticated user

    Returns:
        FilesList: List of files with their metadata
    """
    # Verify project ownership
    project = await session.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get all file chunks for this project
    file_chunks = await session.scalars(
        select(FileContent).where(
            FileContent.project_id == project_id
        )
    )
    file_chunks = file_chunks.all()

    if not file_chunks:
        return FilesList(
            files=[],
            total_files=0,
            total_chunks=0
        )

    # Group chunks by filename
    files_grouped = defaultdict(list)
    for chunk in file_chunks:
        filename = chunk.file_metadata.get('filename', 'unknown')
        files_grouped[filename].append(chunk)

    # Create FileContentPublic objects
    files_list = []
    total_chunks = 0

    for filename, chunks in files_grouped.items():
        # Get the earliest created_at date for this file
        earliest_created = min(chunk.created_at for chunk in chunks)

        files_list.append(FileContentPublic(
            filename=filename,
            chunks_count=len(chunks),
            created_at=earliest_created
        ))

        total_chunks += len(chunks)

    # Sort files by creation date (most recent first)
    files_list.sort(key=lambda x: x.created_at, reverse=True)

    return FilesList(
        files=files_list,
        total_files=len(files_list),
        total_chunks=total_chunks
    )


@router.delete("/files/{project_id}/{filename}")
async def delete_file_from_project(
    project_id: int,
    filename: str,
    session: Session,
    current_user: CurrentUser,
):
    """Delete all chunks of a specific file from a project.

    Args:
        project_id: The project ID
        filename: The filename to delete (URL-encoded)
        session: Database session
        current_user: Authenticated user

    Returns:
        dict: Message with number of chunks deleted
    """
    # Decode filename (in case it has special characters)
    filename = unquote(filename)

    # Verify project ownership
    project = await session.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get all file chunks for this project
    files_to_delete = await session.scalars(
        select(FileContent).where(
            FileContent.project_id == project_id
        )
    )
    files_to_delete = files_to_delete.all()

    # Filter by filename in Python (more reliable than JSON comparison)
    matching_files = [
        f for f in files_to_delete
        if f.file_metadata.get('filename') == filename
    ]

    if not matching_files:
        raise HTTPException(status_code=404, detail="File not found")

    # Delete the matching files
    for file_chunk in matching_files:
        await session.delete(file_chunk)

    await session.commit()

    return {
        "message": f"File '{filename}' deleted successfully",
        "chunks_deleted": len(matching_files),
    }


@router.get('/providers', response_model=LLMProvidersResponse)
async def list_llm_providers():
    """List all available LLM providers and their models.

    Returns:
        LLMProvidersResponse: List of providers with available models
    """
    factory = LLMFactory()
    settings = Settings()

    providers_info = []
    for provider_name in factory.list_providers():
        models = factory.list_models(provider_name)
        providers_info.append(
            LLMProviderInfo(name=provider_name, models=models)
        )

    return LLMProvidersResponse(
        providers=providers_info,
        default_provider=settings.DEFAULT_LLM_PROVIDER,
        default_model=settings.DEFAULT_LLM_MODEL,
    )


@router.post('/stream')
async def chat_with_documents_stream(
    request: ChatRequest,
    session: Session,
    current_user: CurrentUser,
):
    # 1. Verify project ownership
    project = await session.scalar(
        select(Project).where(
            Project.id == request.project_id,
            Project.user_id == current_user.id,
        )
    )
    if not project:
        raise HTTPException(status_code=404, detail='Projeto não encontrado')

    # 2. Handle conversation (new or existing)
    conversation: Conversation
    if request.conversation_id:
        # Resume existing conversation
        conversation = await ConversationService.get_conversation(
            request.conversation_id, session
        )
        if not conversation:
            raise HTTPException(404, 'Conversation not found')

        # Verify conversation belongs to this project
        if conversation.project_id != request.project_id:
            raise HTTPException(
                403,
                'Conversation does not belong to this project'
            )
    else:
        # Create new conversation with auto-generated title
        title = await ConversationService.generate_title_from_message(
            request.query
        )
        conversation = await ConversationService.create_conversation(
            project_id=request.project_id,
            session=session,
            title=title
        )
        await session.commit()

    # 3. Get thread_id from conversation
    thread_id = ConversationService.get_thread_id(conversation.id)

    # 4. Get LLM model from factory
    factory = LLMFactory()
    llm = factory.get_model(request.provider, request.model)
    if not llm:
        raise HTTPException(
            status_code=400,
            detail=f'Provider "{request.provider}" not found'
        )

    # 5. Get checkpointer and create RAG hybrid agent with memory
    checkpointer = get_checkpointer()
    grader_model = factory.get_model('ollama', 'llama3.1')
    agent = create_rag_hybrid_agent(
        llm,
        checkpointer=checkpointer,
        grader_model=grader_model
    )

    # 6. Project context
    context = ProjectContext(
        project_id=request.project_id,
        session=session
    )

    async def event_generator():
        try:
            # Track which tool calls have been sent to avoid duplicates
            sent_tool_call_ids = set()

            # Nodes that should produce visible output to the user
            visible_nodes = {
                'generate_query_or_respond',
                'generate_answer',
                'retrieve',
            }

            # Stream with thread_id for memory
            async for token, metadata in agent.astream(
                {
                    "messages": [
                        {"role": "user", "content": request.query}
                    ]
                },
                context=context,
                stream_mode="messages",
                config={
                    "configurable": {
                        "thread_id": thread_id
                    }
                }
            ):
                # Get the node that produced this message
                node_name = metadata.get('langgraph_node', '')

                # Only allow messages from explicit visible nodes
                if node_name not in visible_nodes:
                    continue

                # 1. Tool call (modelo requisitando ferramenta)
                if getattr(token, "tool_calls", None):
                    for tool_call in token.tool_calls:
                        tool_id = tool_call.get("id")
                        # Only send if we haven't sent this tool call yet
                        if tool_id and tool_id not in sent_tool_call_ids:
                            sent_tool_call_ids.add(tool_id)
                            data = {
                                "type": "tool_call",
                                "tool_name": tool_call.get("name"),
                                "tool_id": tool_id,
                                "args": tool_call.get("args", {})
                            }
                            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"  # noqa: E501

                # 2. Tool result (retorno da ferramenta)
                elif isinstance(token, ToolMessage):
                    data = {
                        "type": "tool_result",
                        "tool_name": token.name,
                        "content": str(token.content)
                    }
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

                # 3. Texto normal do modelo
                elif token.content:
                    data = {
                        "type": "token",
                        "content": token.content
                    }
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

            # Done signal with conversation_id
            data = {
                "type": "done",
                "conversation_id": conversation.id
            }
            yield f"data: {json.dumps(data)}\n\n"

        # except Exception as exc:
        #     yield f"\n[ERRO]: {exc}"
        except Exception as exc:
            data = {
                "type": "error",
                "message": str(exc)
            }
            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Conversation-ID": str(conversation.id),
        }
    )


# ==========================================
# Conversation Management Endpoints
# ==========================================

@router.get('/conversations/{project_id}', response_model=ConversationList)
async def list_conversations(
    project_id: int,
    session: Session,
    current_user: CurrentUser,
    limit: int = 50,
    offset: int = 0,
):
    """List all conversations for a project."""
    # Verify project ownership
    project = await session.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
    )
    if not project:
        raise HTTPException(404, 'Project not found')

    conversations = await ConversationService.list_conversations(
        project_id, session, limit, offset
    )

    total = await session.scalar(
        select(func.count(Conversation.id)).where(
            Conversation.project_id == project_id
        )
    )

    return ConversationList(conversations=conversations, total=total or 0)


@router.post(
    '/conversations/{project_id}',
    response_model=ConversationPublic,
    status_code=201
)
async def create_conversation(
    project_id: int,
    data: ConversationCreate,
    session: Session,
    current_user: CurrentUser,
):
    """Create new conversation."""
    project = await session.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
    )
    if not project:
        raise HTTPException(404, 'Project not found')

    title = data.title or 'New Conversation'
    conversation = await ConversationService.create_conversation(
        project_id, session, title
    )
    await session.commit()
    return conversation


@router.patch(
    '/conversations/{conversation_id}',
    response_model=ConversationPublic
)
async def update_conversation(
    conversation_id: int,
    data: ConversationUpdate,
    session: Session,
    current_user: CurrentUser,
):
    """Update conversation title."""
    conversation = await ConversationService.get_conversation(
        conversation_id, session
    )
    if not conversation:
        raise HTTPException(404, 'Conversation not found')

    # Verify ownership through project
    project = await session.scalar(
        select(Project).where(
            Project.id == conversation.project_id,
            Project.user_id == current_user.id,
        )
    )
    if not project:
        raise HTTPException(403, 'Not authorized')

    updated = await ConversationService.update_conversation_title(
        conversation_id, data.title, session
    )
    await session.commit()
    return updated


@router.delete('/conversations/{conversation_id}', status_code=204)
async def delete_conversation(
    conversation_id: int,
    session: Session,
    current_user: CurrentUser,
):
    """Delete conversation and checkpoints."""
    conversation = await ConversationService.get_conversation(
        conversation_id, session
    )
    if not conversation:
        raise HTTPException(404, 'Conversation not found')

    project = await session.scalar(
        select(Project).where(
            Project.id == conversation.project_id,
            Project.user_id == current_user.id,
        )
    )
    if not project:
        raise HTTPException(403, 'Not authorized')

    thread_id = ConversationService.get_thread_id(conversation_id)

    # Delete conversation
    await ConversationService.delete_conversation(conversation_id, session)

    # Commit conversation deletion first
    await session.commit()

    # Delete checkpoints (best effort, separate transaction)
    try:
        await session.execute(
            text('DELETE FROM checkpoints WHERE thread_id = :thread_id'),
            {'thread_id': thread_id}
        )
        await session.execute(
            text(
                'DELETE FROM checkpoint_writes WHERE thread_id = :thread_id'
            ),
            {'thread_id': thread_id}
        )
        await session.commit()
    except Exception:
        # Rollback only the checkpoint deletion, not the conversation
        await session.rollback()


def _normalize_message_role(msg) -> str:
    """
    Normalize LangChain message types to frontend-friendly roles.
    """
    msg_type = None

    if hasattr(msg, 'type'):
        msg_type = msg.type
    elif hasattr(msg, '__class__'):
        msg_type = msg.__class__.__name__.lower()

    if not msg_type:
        return 'unknown'

    if 'human' in msg_type or 'user' in msg_type:
        return 'user'
    if 'ai' in msg_type or 'assistant' in msg_type:
        return 'assistant'
    if 'system' in msg_type:
        return 'system'
    if 'tool' in msg_type:
        return 'tool'

    return 'unknown'


@router.get(
    '/conversations/{conversation_id}/history',
    response_model=dict
)
async def get_conversation_history(
    conversation_id: int,
    session: Session,
    current_user: CurrentUser,
):
    """
    Return conversation message history from LangChain checkpoints.
    """

    # 1 - Load conversation
    conversation = await ConversationService.get_conversation(
        conversation_id, session
    )
    if not conversation:
        raise HTTPException(404, 'Conversation not found')

    # 2 - Verify ownership via project
    project = await session.scalar(
        select(Project).where(
            Project.id == conversation.project_id,
            Project.user_id == current_user.id,
        )
    )
    if not project:
        raise HTTPException(403, 'Not authorized')

    # 3 - Resolve thread_id
    thread_id = ConversationService.get_thread_id(conversation.id)

    # 4 - Get checkpointer
    checkpointer = get_checkpointer()

    # 5 - Fetch history from LangChain
    try:
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        state = await checkpointer.aget_tuple(config)

        messages_out = []

        if state and state.checkpoint:
            channel_values = state.checkpoint.get(
                'channel_values', {}
            )
            messages = channel_values.get('messages', [])

            for msg in messages:
                role = _normalize_message_role(msg)
                content = getattr(msg, 'content', None)

                if content:
                    messages_out.append(
                        {
                            "role": role,
                            "content": content,
                        }
                    )

        return {
            "conversation_id": conversation.id,
            "messages": messages_out,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f'Failed to load conversation history: {exc}'
        )
