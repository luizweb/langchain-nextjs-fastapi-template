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
