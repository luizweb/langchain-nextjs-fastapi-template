from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.settings import Settings

settings = Settings()

engine = create_async_engine(settings.DATABASE_URL)

# Convert DATABASE_URL for checkpointer (psycopg uses postgresql://)
checkpointer_url = settings.DATABASE_URL.replace(
    'postgresql+psycopg://',
    'postgresql://'
)


class CheckpointerManager:
    """Manager for AsyncPostgresSaver singleton instance."""

    def __init__(self):
        self._checkpointer: AsyncPostgresSaver | None = None

    async def initialize(self):
        """Initialize AsyncPostgresSaver and create tables.

        Called once at application startup via lifespan event.
        This keeps the connection alive for the entire app lifetime.
        """
        if self._checkpointer is None:
            try:
                # Create and enter checkpointer context
                # We keep it alive for the entire app lifetime
                # Note: We manually manage context lifecycle to keep connection
                # open across requests, which is why we use __aenter__ directly
                conn = AsyncPostgresSaver.from_conn_string(checkpointer_url)
                self._checkpointer = await conn.__aenter__()  # type: ignore[attr-defined]  # noqa: PLC2801
                # Store cleanup method for later
                self._cleanup = lambda: conn.__aexit__(None, None, None)
                # Initialize tables
                await self._checkpointer.setup()
                print('✓ AsyncPostgresSaver initialized')
            except Exception as e:
                print(f'✗ Failed to initialize checkpointer: {e}')
                raise

    async def cleanup(self):
        """Cleanup checkpointer on app shutdown."""
        if hasattr(self, '_cleanup'):
            try:
                await self._cleanup()
                print('✓ AsyncPostgresSaver cleaned up')
            except Exception as e:
                print(f'✗ Failed to cleanup checkpointer: {e}')

    def get(self) -> AsyncPostgresSaver:
        """Get checkpointer instance.

        Raises:
            RuntimeError: If checkpointer not initialized
        """
        if self._checkpointer is None:
            raise RuntimeError('Checkpointer not initialized')
        return self._checkpointer


# Singleton instance
_checkpointer_manager = CheckpointerManager()


async def initialize_checkpointer():
    """Initialize checkpointer via manager."""
    await _checkpointer_manager.initialize()


async def cleanup_checkpointer():
    """Cleanup checkpointer via manager."""
    await _checkpointer_manager.cleanup()


def get_checkpointer() -> AsyncPostgresSaver:
    """Get checkpointer instance via manager."""
    return _checkpointer_manager.get()


async def get_session():  # pragma: no cover
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session
