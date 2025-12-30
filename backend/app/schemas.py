from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Message(BaseModel):
    message: str


class UserSchema(BaseModel):
    username: str
    email: EmailStr
    password: str
    is_admin: bool = False


class UserPublic(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_admin: bool
    # Permite que o schema aceite objetos do SQLAlchemy (ORM)
    model_config = ConfigDict(from_attributes=True)


class UserList(BaseModel):
    users: list[UserPublic]


class Token(BaseModel):
    access_token: str
    token_type: str


class FilterPage(BaseModel):
    offset: int = Field(0, ge=0)
    limit: int = Field(100, ge=1)


class ProjectCreate(BaseModel):
    title: str
    description: str = ''
    llm_prompt: str = ''


class ProjectPublic(BaseModel):
    id: int
    user_id: int
    title: str
    description: str
    llm_prompt: str
    model_config = ConfigDict(from_attributes=True)


class ProjectList(BaseModel):
    projects: list[ProjectPublic]


class FileContentPublic(BaseModel):
    """Schema para informações de um arquivo (agrupado por filename)."""
    filename: str
    chunks_count: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class FilesList(BaseModel):
    """Schema para listar todos os arquivos de um projeto."""
    files: list[FileContentPublic]
    total_files: int
    total_chunks: int


class ChatRequest(BaseModel):
    """Schema para request do chat."""
    query: str = Field(..., description="Query para buscar nos documentos")
    project_id: int = Field(
        ...,
        description="ID do projeto para buscar documentos"
    )


# class ChatResponse(BaseModel):
#     """Schema para response do chat."""
#     answer: str = Field(..., description="Resposta do agente RAG")
#     query: str = Field(..., description="Query original")
#     project_id: int = Field(..., description="ID do projeto")
