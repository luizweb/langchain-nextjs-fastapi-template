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

import asyncio
"""
from typing import Annotated, Any, Dict, List, Optional

from fastapi import Depends
from sqlalchemy import insert, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import FileContent
from app.services.embedding_service import EmbeddingService

Session = Annotated[AsyncSession, Depends(get_session)]


class FileContentService:
    """Service for FileContent database operations."""

    @classmethod
    async def bulk_create(
        cls,
        records: List[Dict[str, Any]],
        session: Session,
    ) -> int:
        """
        Bulk insert FileContent records.

        Returns:
            Number of records inserted
        """
        if not records:
            return 0

        await session.execute(insert(FileContent), records)
        await session.commit()

        return len(records)

    @classmethod
    async def search_similar(
        cls,
        query: str,
        session: Session,
        project_id: int,
        limit: int = 2,
        similarity_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar file contents using vector similarity."""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        try:
            embedding = EmbeddingService.embed_query(query)
            # Calculate cosine similarity (1 - cosine_distance)
            # 1 = very similar, 0 = completely different
            similarity_expr = 1 - FileContent.embedding.cosine_distance(
                embedding
            )

            stmt = (
                select(
                    FileContent.id,
                    FileContent.content,
                    FileContent.file_metadata,
                    similarity_expr.label("similarity_score"),
                )
                .where(FileContent.project_id == project_id)
                .order_by(similarity_expr.desc())  # descending similarity
                .limit(limit)
            )

            if similarity_threshold is not None:
                stmt = stmt.where(similarity_expr >= similarity_threshold)

            result = await session.execute(stmt)
            rows = result.all()

            return [cls._format_result(row) for row in rows]

        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Database error: {str(e)}")

    @staticmethod
    def _format_result(row) -> Dict[str, Any]:
        """Format query result."""
        return {
            "id": row.id,
            "content": row.content,
            "metadata": row.file_metadata,
            "similarity_score": round(float(row.similarity_score), 4),
        }

    @classmethod
    def format_for_llm(cls, file_contents: List[Dict[str, Any]]) -> str:
        """Format file contents for LLM context."""
        if not file_contents:
            return "Nenhum conteúdo relevante encontrado."

        formatted_parts = []
        for idx, fc in enumerate(file_contents, 1):
            metadata = fc.get("metadata", {})
            formatted_parts.append(
                f"[Documento {idx}]\n"
                f"Arquivo: {metadata.get('filename', 'unknown')}\n"
                f"Similaridade: {fc['similarity_score']:.2%}\n"
                f"Conteúdo:\n{fc['content']}\n"
            )

        return "\n---\n".join(formatted_parts)


# # --- Exemplo de uso ---
# async def exemplo_busca_semantica():
#     """
#     Exemplo completo de uso da busca semântica.

#     Este exemplo demonstra:
#     1. Inserção de dados de teste
#     2. Busca semântica com diferentes queries
#     3. Formatação para LLM
#     4. Execução interativa no VSCode
#     """
#     from app.database import engine  # noqa: PLC0415

#     print("🔍 Exemplo de Busca Semântica com FileContentService")
#     print("=" * 60)

#     PROJECT_ID = 4

#     async with AsyncSession(engine) as session:
#         try:
#             # 1. Inserir dados de teste
#             print("\n📝 1. Inserindo dados de teste...")

#             test_records = [
#                 {
#                     "content": "O Python é uma linguagem de programação de alto nível, dinâmica e interpretada.",  # noqa: E501
#                     "project_id": PROJECT_ID,
#                     "file_metadata": {
#                         "filename": "python_intro.txt",
#                         "chunk_index": 0,
#                         "total_chunks": 3
#                     },
#                     "embedding": EmbeddingService.embed_documents([
#                         "O Python é uma linguagem de programação de alto nível, dinâmica e interpretada."  # noqa: E501
#                     ])[0]
#                 },
#                 {
#                     "content": "FastAPI é um framework web moderno e rápido para construir APIs com Python.",  # noqa: E501
#                     "project_id": PROJECT_ID,
#                     "file_metadata": {
#                         "filename": "fastapi_guide.txt",
#                         "chunk_index": 0,
#                         "total_chunks": 2
#                     },
#                     "embedding": EmbeddingService.embed_documents([
#                         "FastAPI é um framework web moderno e rápido para construir APIs com Python."  # noqa: E501
#                     ])[0]
#                 },
#                 {
#                     "content": "Machine Learning é um subcampo da inteligência artificial que permite aos computadores aprender.",  # noqa: E501
#                     "project_id": PROJECT_ID,
#                     "file_metadata": {
#                         "filename": "ml_basics.txt",
#                         "chunk_index": 0,
#                         "total_chunks": 5
#                     },
#                     "embedding": EmbeddingService.embed_documents([
#                         "Machine Learning é um subcampo da inteligência artificial que permite aos computadores aprender."  # noqa: E501
#                     ])[0]
#                 }
#             ]

#             inserted = await FileContentService.bulk_create(
#                 records=test_records,
#                 session=session
#             )
#             print(f"✅ {inserted} registros inseridos com sucesso!")

#             # 2. Realizar buscas semânticas
#             queries = [
#                 "linguagem de programação python",
#                 "framework para APIs",
#                 "inteligência artificial e aprendizado"
#             ]

#             for i, query in enumerate(queries, 1):
#                 print(f"\n🔎 {i}. Busca: '{query}'")
#                 print("-" * 40)

#                 # Busca semântica
#                 results = await FileContentService.search_similar(
#                     query=query,
#                     session=session,
#                     project_id=PROJECT_ID,
#                     limit=3,
#                     similarity_threshold=0.1
#                 )

#                 if results:
#                     print(f"📊 Encontrados {len(results)} resultados:")

#                     for j, result in enumerate(results, 1):
#                         print(f"\n   Resultado {j}:")
#                         print(f"   📄 : {result['metadata']['filename']}")
#                         print(f"   🎯 %: {result['similarity_score']:.2%}")
#                         print(f"   📝 : {result['content'][:100]}...")
#                 else:
#                     print("❌ Nenhum resultado encontrado.")

#                 # 3. Formatação para LLM
#                 if results:
#                     print("\n🤖 Formatação para LLM:")
#                     print("-" * 30)
#                     formatted = FileContentService.format_for_llm(results)
#                     print(formatted)

#                 print("\n" + "=" * 60)

#             print("\n✅ Exemplo de busca semântica concluído!")

#         except ValueError as e:
#             print(f"❌ Erro de validação: {e}")
#         except SQLAlchemyError as e:
#             print(f"❌ Erro no banco: {e}")
#         except Exception as e:
#             print(f"❌ Erro inesperado: {e}")


# # --- Execução interativa para VSCode ---
# if __name__ == "__main__":
#     # Para execução normal (terminal)
#     asyncio.run(exemplo_busca_semantica())
# else:
#     # Para execução interativa no VSCode
#     # Execute: await exemplo_busca_semantica() no console Python
#     print("📌 Para execução interativa no VSCode, execute:")
#     print("   await exemplo_busca_semantica()")
