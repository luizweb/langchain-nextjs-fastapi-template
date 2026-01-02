# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Full-stack AI application combining Next.js frontend with FastAPI backend. The application implements a RAG (Retrieval-Augmented Generation) system that allows users to upload PDFs, process them into searchable chunks with embeddings, and chat with documents using LangChain agents.

## Architecture

### Backend (FastAPI + LangChain)

**Core Stack:**
- FastAPI for REST API
- PostgreSQL with pgvector extension for vector storage
- SQLAlchemy 2.0 (async) for ORM
- Alembic for migrations
- LangChain for RAG agent implementation
- JWT authentication with password hashing (argon2)

**Key Components:**

1. **Database Models** (`app/models.py`):
   - `User`: User authentication and profile
   - `Project`: User projects containing documents
   - `FileContent`: Document chunks with embeddings (1024-dimensional vectors)
   - Relationships: User → Projects → FileContents

2. **RAG Agent** (`app/agents/rag.py`):
   - Uses LangChain's `create_agent` with tool-based architecture
   - `search_project_documents` tool for semantic search
   - Streams responses with tool calls and results
   - Integrates with ChatOllama (model: "gpt-oss:120b-cloud")
   - Uses `ProjectContext` to maintain project and session state

3. **Services Layer**:
   - `PDFProcessingService`: Extracts and chunks PDF content using pymupdf4llm
   - `FileContentService`: Handles embeddings and similarity search
   - `EmbeddingService`: Generates embeddings using sentence-transformers

4. **Routers** (`app/routers/`):
   - `auth.py`: Login, token generation
   - `users.py`: User CRUD operations
   - `projects.py`: Project management
   - `chat.py`: PDF upload, file management, streaming chat with RAG agent

5. **Database Connection**:
   - Async engine created from `Settings().DATABASE_URL`
   - Session management via `get_session()` dependency

### Frontend (Next.js 16 + React 19)

**Core Stack:**
- Next.js 16 with App Router
- React 19
- TypeScript
- Tailwind CSS 4
- shadcn/ui components (Radix UI primitives)
- Server-Sent Events for streaming chat

**Structure:**
- `app/`: Route-based pages using App Router convention
  - `/login`, `/register`: Authentication pages
  - `/profile`: User profile management
  - `/admin/users`: Admin user management
  - `/projects`: Project listing and management
  - `/projects/chat`: Chat interface for RAG interactions
  - `/password-recovery`: Password reset flow
- `components/`: Reusable React components
- `components/ui/`: shadcn/ui component library
- `hooks/`: Custom React hooks
- `lib/`: Utility functions

## Common Commands

### Backend

**Development:**
```bash
cd backend
uv sync  # Install dependencies
task run  # Start FastAPI dev server (http://localhost:8000)
```

**Database:**
```bash
# Start PostgreSQL with pgvector
docker compose up langchain-nextjs-fastapi_database -d

# Create migration
alembic revision --autogenerate -m "description"

# Run migrations
alembic upgrade head
```

**Testing:**
```bash
cd backend
task test  # Run tests with coverage (auto-runs lint first)
task lint  # Run ruff linting
task format  # Format code with ruff
```

**Run single test:**
```bash
pytest tests/test_file.py::test_function_name -v
```

### Frontend

**Development:**
```bash
cd frontend
npm install  # Install dependencies
npm run dev  # Start Next.js dev server (http://localhost:3000)
```

**Build:**
```bash
npm run build  # Production build
npm start  # Start production server
```

**Linting:**
```bash
npm run lint  # Run ESLint
```

**Add shadcn/ui component:**
```bash
npx shadcn@latest add [component-name]
```

## Development Patterns

### Backend Patterns

1. **Authentication Flow:**
   - JWT tokens with bearer authentication
   - Dependencies: `get_current_user` from `app.security`
   - User context: `CurrentUser = Annotated[User, Depends(get_current_user)]`

2. **Database Session:**
   - Always use async session: `Session = Annotated[AsyncSession, Depends(get_session)]`
   - Use SQLAlchemy 2.0 syntax (not legacy query API)

3. **RAG Streaming Pattern:**
   - Agent streams events in "messages" mode
   - Three event types: `tool_call`, `tool_result`, `token`
   - Return `StreamingResponse` with `text/event-stream` media type
   - Format: `data: {json}\n\n` for SSE protocol

4. **Service Layer:**
   - Services handle business logic, not routers
   - Services are stateless with static/class methods
   - Example: `FileContentService.search_similar()`, `PDFProcessingService.process_pdf_file()`

5. **Testing:**
   - Uses pytest with asyncio support
   - Factory Boy for test fixtures
   - Testcontainers for database isolation
   - Coverage reports in `htmlcov/`

### Frontend Patterns

1. **App Router Convention:**
   - `page.tsx`: Route page component
   - `layout.tsx`: Shared layout wrapper
   - Folder structure maps to URL paths

2. **Styling:**
   - Tailwind CSS with custom configuration
   - shadcn/ui for pre-built components
   - Global styles in `app/globals.css`

3. **Component Organization:**
   - UI primitives in `components/ui/` (shadcn)
   - Custom components in `components/`
   - Use Radix UI primitives through shadcn abstractions

## Code Quality Standards

### Backend (Ruff Configuration)

- Line length: 79 characters
- Quote style: Single quotes
- Linting rules: I (imports), F (pyflakes), E/W (pycodestyle), PL (pylint), PT (pytest), FAST
- Migrations folder excluded from linting

### Environment Variables

Required in `backend/.env`:
```
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/dbname
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Key Implementation Details

1. **Vector Search:**
   - Uses pgvector extension for PostgreSQL
   - Embeddings: 1024-dimensional vectors (sentence-transformers)
   - Similarity search via cosine distance in SQL

2. **PDF Processing:**
   - Files processed in-memory (not stored permanently)
   - Chunks extracted with metadata (filename, page, etc.)
   - Each chunk gets embedded and stored in `file_contents` table

3. **Agent Tool System:**
   - Tools receive `ToolRuntime[ProjectContext]` with project_id and session
   - Tools must be async functions
   - Tool results automatically sent back to agent for final response

4. **CORS Configuration:**
   - Backend allows all origins (`allow_origins=["*"]`)
   - Configure appropriately for production deployments

## Testing Strategy

- Backend tests use async patterns throughout
- Database tests use testcontainers for isolation
- Coverage reports generated post-test in `htmlcov/`
- Pre-test hook runs linting automatically
- Tests are located in `backend/tests/` mirroring app structure
