# import logging
import json
import tempfile
from collections import defaultdict
from typing import Annotated
from urllib.parse import unquote

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse  # texto incremental
from langchain_core.messages import ToolMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.rag import ProjectContext, agent
from app.database import get_session
from app.models import FileContent, Project, User
from app.schemas import ChatRequest, FileContentPublic, FilesList
from app.security import get_current_user
from app.services import FileContentService, PDFProcessingService

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


@router.post("/stream")
async def chat_with_documents_stream(
    request: ChatRequest,
    session: Session,
    current_user: CurrentUser,
):
    # 1. Verifica se o projeto pertence ao usuário
    project = await session.scalar(
        select(Project).where(
            Project.id == request.project_id,
            Project.user_id == current_user.id,
        )
    )
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    # 2. Verifica se o projeto tem documentos
    file_exists = await session.scalar(
        select(FileContent)
        .where(FileContent.project_id == request.project_id)
        .limit(1)
    )
    if not file_exists:
        raise HTTPException(
            status_code=400,
            detail="Projeto não possui documentos"
        )

    # 3. Contexto do agente
    context = ProjectContext(
        project_id=request.project_id,
        session=session
    )

    async def event_generator():
        try:
            # tool_results = {}

            async for token, metadata in agent.astream(
                {
                    "messages": [
                        {"role": "user", "content": request.query}
                    ]
                },
                context=context,
                stream_mode="messages",
            ):

                # 1️⃣ Tool call (modelo requisitando ferramenta)
                if getattr(token, "tool_calls", None):
                    # for tool_call in token.tool_calls:
                    #     print(f"[tool_call] {tool_call['name']}")
                    for tool_call in token.tool_calls:
                        data = {
                            "type": "tool_call",
                            "tool_name": tool_call.get("name"),
                            "tool_id": tool_call.get("id"),
                            "args": tool_call.get("args", {})
                        }
                        yield f"data: {json.dumps(data, ensure_ascii=False)}\n"

                # 2️⃣ Tool result (retorno da ferramenta)
                elif isinstance(token, ToolMessage):
                    # tool_results[token.tool_call_id] = {
                    #     "tool_name": token.name,
                    #     "content": token.content,
                    # }
                    # # ❌ não printa
                    # continue
                    data = {
                        "type": "tool_result",
                        "tool_name": token.name,
                        "content": str(token.content)
                    }
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

                # 3️⃣ Texto normal do modelo
                elif token.content:
                    # print(token.content, end="", flush=True)
                    data = {
                        "type": "token",
                        "content": token.content
                    }
                    # ✅ AQUI está o yield que faltava!
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

            # Sinal de conclusão
            data = {"type": "done"}
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
        # media_type="text/plain; charset=utf-8"
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
