
from pathlib import Path

import chromadb
from pypdf import PdfReader
from docx import Document
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter


# Project directories
BASE_DIR = Path(__file__).resolve().parents[2]
CHROMA_DIR = BASE_DIR / "data" / "chroma_db"

# Initialize embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Initialize persistent ChromaDB
chroma_client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)

collection = chroma_client.get_or_create_collection(
    name="rag_documents",
    metadata={"hnsw:space": "cosine"}
)

# Text chunking configuration
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=150
)


def extract_text(file_path: Path):

    documents = []

    extension = file_path.suffix.lower()

    if extension == ".pdf":

        reader = PdfReader(str(file_path))

        for page_number, page in enumerate(reader.pages, start=1):

            text = page.extract_text() or ""

            if text.strip():
                documents.append({
                    "text": text,
                    "page": page_number
                })

    elif extension == ".docx":

        doc = Document(str(file_path))

        text = "\n".join(
            paragraph.text
            for paragraph in doc.paragraphs
            if paragraph.text.strip()
        )

        if text.strip():
            documents.append({
                "text": text,
                "page": None
            })

    else:
        raise ValueError("Unsupported document format.")

    return documents


def process_document(file_path: Path, file_hash: str, filename: str):

    # Extract text
    documents = extract_text(file_path)

    if not documents:
        raise ValueError("No readable text found in document.")

    # Create chunks
    all_chunks = []

    for document in documents:

        split_chunks = text_splitter.split_text(
            document["text"]
        )

        for chunk_text in split_chunks:

            all_chunks.append({
                "text": chunk_text,
                "page": document["page"]
            })

    if not all_chunks:
        raise ValueError("No text chunks could be generated.")

    # Generate embeddings
    texts = [chunk["text"] for chunk in all_chunks]

    embeddings = embedding_model.encode(
        texts,
        show_progress_bar=False
    ).tolist()

    # Store in ChromaDB
    ids = [
        f"{file_hash}_{index}"
        for index in range(len(all_chunks))
    ]

    metadatas = [
        {
            "file_hash": file_hash,
            "filename": filename,
            "page": chunk["page"] or 0,
            "chunk_position": index
        }
        for index, chunk in enumerate(all_chunks)
    ]

    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

    return {
        "filename": filename,
        "file_hash": file_hash,
        "chunks_created": len(all_chunks)
    }
