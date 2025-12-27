from typing import Any, Dict, List

import pymupdf
import pymupdf4llm
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

model_name = "BAAI/bge-m3"
# Optional:
model_kwargs = {"device": "cpu"}  # or "cuda" if you have a compatible GPU
encode_kwargs = {"normalize_embeddings": False}

embedding_model = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)


def pdf_para_markdown(caminho_pdf: str) -> str:
    """
    Converte um arquivo PDF para formato Markdown.

    Args:
        caminho_pdf (str): Caminho para o arquivo PDF de entrada

    Returns:
        str: Conteúdo do PDF convertido em formato Markdown
    """
    doc = pymupdf.open(caminho_pdf)
    md = pymupdf4llm.to_markdown(doc)
    doc.close()  # Liberar recursos
    return md


def criar_documento_langchain(texto: str, source: str) -> Document:
    """
    Cria um documento do LangChain com texto e metadado de source.

    Args:
        texto (str): Conteúdo do documento
        source (str): Fonte/origem do documento para os metadados

    Returns:
        Document: Objeto Document do LangChain
    """
    documento = Document(
        page_content=texto,
        metadata={"source": source}
    )
    return documento


def dividir_documentos(
    documentos,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    add_start_index: bool = True
) -> List[Document]:
    """
    Divide documentos do LangChain em chunks menores.

    Args:
        documentos (list ou Document): Documento(s) do LangChain para dividir
        chunk_size (int): Tamanho de cada chunk em caracteres (padrão: 1000)
        chunk_overlap (int): Sobreposição entre chunks em caracteres
        add_start_index (bool): Se True, adiciona índice do documento original

    Returns:
        list: Lista de documentos divididos em chunks
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=add_start_index,
    )

    # Aceita tanto um documento único quanto uma lista
    if not isinstance(documentos, list):
        documentos = [documentos]

    chunks = text_splitter.split_documents(documentos)

    return chunks


def preparar_chunks_para_banco(
        chunks: List[Any],
        project_id: int
    ) -> List[Dict[str, Any]]:
    """
    Processa chunks e retorna dicionários prontos para inserção no BD.
    Utiliza processamento em batch para otimizar a geração de embeddings.

    Args:
        chunks: Lista de chunks brutos do LangChain
        project_id (int): ID do projeto para associação

    Returns:
        List[Dict[str, Any]]: Lista de dicionários no formato do modelo Files
    """
    registros_processados = []

    try:
        # Extrair todos os textos e processar embeddings em batch
        textos = [
            chunk.page_content.replace("\n", " ").strip() for chunk in chunks
        ]

        # Gerar embeddings em batch
        embeddings = embedding_model.embed_documents(textos)

        # Processar cada chunk com seu embedding
        for chunk, embedding in zip(chunks, embeddings):
            filename = chunk.metadata.get("source", "unknown")

            registro = {
                "project_id": project_id,
                "file_metadata": {
                    "filename": filename,
                },
                "content": chunk.page_content.strip(),
                "embedding": embedding,
            }

            registros_processados.append(registro)

    except Exception as e:
        print(f"Erro ao processar chunks em batch: {e}")
        print("Tentando processamento individual...")

        # Fallback para processamento individual
        for i, chunk in enumerate(chunks):
            try:
                texto = chunk.page_content.replace("\n", " ").strip()
                embedding = embedding_model.embed_query(texto)

                registro = {
                    "project_id": project_id,
                    "file_metadata": {
                        "filename": chunk.metadata.get("source", "unknown"),
                    },
                    "content": chunk.page_content.strip(),
                    "embedding": embedding,
                }
                registros_processados.append(registro)

                if (i + 1) % 10 == 0:
                    print(f"Processados {i + 1}/{len(chunks)} chunks...")

            except Exception as e:
                print(f"Erro ao processar chunk {i}: {e}")
                continue

    return registros_processados


# Exemplo de uso
if __name__ == "__main__":
    arquivo_pdf = "input.pdf"
    markdown = pdf_para_markdown(arquivo_pdf)
    document = criar_documento_langchain(
        texto=markdown,
        source=arquivo_pdf
    )
    chunks = dividir_documentos(document)
    registros = preparar_chunks_para_banco(chunks, project_id=123)
