import tempfile
from collections import defaultdict
from typing import Annotated
from urllib.parse import unquote

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import FileContent, Project, User
from app.schemas import FileContentPublic, FilesList
from app.security import get_current_user
from app.utils import (
    criar_documento_langchain,
    dividir_documentos,
    pdf_para_markdown,
    preparar_chunks_para_banco,
)

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
    """Upload a PDF, process it with LangChain utils and store chunks in DB.

    The PDF is *not* persisted on disk; it is read into memory, written to a
    temporary file only for the duration of processing, and then discarded.
    """
    # Validate content type (basic check)
    if uploaded_file.content_type not in {
        "application/pdf",
        "application/x-pdf"
    }:
        raise HTTPException(status_code=400, detail="File must be a PDF")

    # Ensure the project belongs to the current user
    project = await session.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    # Read PDF contents into memory (no permanent storage)
    file_bytes = await uploaded_file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    # Use a temporary file only for the duration of pdf_para_markdown
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
            tmp.write(file_bytes)
            tmp.flush()

            markdown = pdf_para_markdown(tmp.name)
    except Exception as exc:  # pragma: no cover - depends on PDF internals
        raise HTTPException(
            status_code=500,
            detail=f"Error processing PDF: {exc}"
        )

    # Build LangChain document and split into chunks
    document = criar_documento_langchain(
        texto=markdown,
        source=uploaded_file.filename
        )
    chunks = dividir_documentos(document)

    # Prepare records for DB and bulk insert
    processed_records = preparar_chunks_para_banco(
        chunks,
        project_id=project_id
    )
    if not processed_records:
        raise HTTPException(
            status_code=400,
            detail="No content extracted from PDF"
        )

    # Bulk insert using async session
    await session.execute(insert(FileContent), processed_records)
    await session.commit()

    return {
        "message": "PDF processed successfully",
        "chunks_inserted": len(processed_records),
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
