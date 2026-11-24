
import hashlib
import logging
from pathlib import Path
from app.rag.service import rag_answer
from fastapi import FastAPI, UploadFile, File, HTTPException

#from app.ingestion.processor import process_document
from app.ingestion.processor import process_document, collection
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Production RAG Service",
    description="A document-based question answering system",
    version="1.0.0"
)

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 20 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


@app.get("/")
def home():
    return {"message": "Production RAG Service is running!"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):

    original_filename = Path(file.filename or "").name
    extension = Path(original_filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are allowed."
        )

    file_content = await file.read()

    if not file_content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size exceeds the 20 MB limit."
        )

    file_hash = hashlib.sha256(file_content).hexdigest()

    existing_file = list(UPLOAD_DIR.glob(f"{file_hash}_*"))

    if existing_file:
        raise HTTPException(
            status_code=409,
            detail="This document has already been uploaded."
        )

    safe_filename = original_filename.replace(" ", "_")
    stored_filename = f"{file_hash}_{safe_filename}"
    stored_path = UPLOAD_DIR / stored_filename

    stored_path.write_bytes(file_content)

    try:
        processing_result = process_document(
            file_path=stored_path,
            file_hash=file_hash,
            filename=original_filename
        )

    except ValueError as exc:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=422,
            detail=str(exc)
        )

    except Exception:
        stored_path.unlink(missing_ok=True)
        logger.exception("Document processing failed")
        raise HTTPException(
            status_code=500,
            detail="Document processing failed."
        )

    return {
        "message": "Document uploaded and processed successfully.",
        "filename": original_filename,
        "file_hash": file_hash,
        "stored_filename": stored_filename,
        "processing": processing_result
    }


@app.get("/documents")
def list_documents():

    result = collection.get(include=["metadatas"])

    documents = {}

    for metadata in result["metadatas"]:

        file_hash = metadata.get("file_hash")
        filename = metadata.get("filename", "Unknown")

        # Support older records without file hashes
        document_key = file_hash or f"legacy:{filename}"

        if document_key not in documents:
            documents[document_key] = {
                "filename": filename,
                "file_hash": file_hash,
                "chunks_count": 0
            }

        documents[document_key]["chunks_count"] += 1

    return {
        "total_documents": len(documents),
        "documents": list(documents.values())
    }


@app.delete("/documents/{file_hash}")
def delete_document(file_hash: str):

    # Find all chunks belonging to this document
    result = collection.get(
        where={"file_hash": file_hash},
        include=["metadatas"]
    )

    if not result["ids"]:
        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    # Delete all corresponding vectors from ChromaDB
    collection.delete(
        where={"file_hash": file_hash}
    )

    # Delete the uploaded file
    matching_files = list(
        UPLOAD_DIR.glob(f"{file_hash}_*")
    )

    for file_path in matching_files:
        file_path.unlink(missing_ok=True)

    return {
        "message": "Document and its vectors deleted successfully.",
        "file_hash": file_hash,
        "deleted_chunks": len(result["ids"])
    }

from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000
    )


@app.post("/ask")
def ask_question(request: QuestionRequest):

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    try:
        result = rag_answer(question)

        return {
            "question": question,
            "answer": result["answer"],
            "sources": result["sources"]
        }

    except Exception:
        logger.exception("Question answering failed")

        raise HTTPException(
            status_code=500,
            detail="Unable to process the question."
        )
