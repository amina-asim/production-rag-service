
import hashlib

import pytest
from fastapi.testclient import TestClient

import app.main as main

client = TestClient(main.app)


def test_home_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Production RAG Service is running!"


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_list_documents_endpoint(monkeypatch):
    class FakeCollection:
        def get(self, **kwargs):
            return {
                "metadatas": [
                    {"filename": "sample.pdf", "file_hash": "abc"},
                    {"filename": "sample.pdf", "file_hash": "abc"},
                    {"filename": "legacy.pdf"},
                ]
            }

    monkeypatch.setattr(main, "collection", FakeCollection())

    response = client.get("/documents")

    assert response.status_code == 200
    assert response.json()["total_documents"] == 2


def test_ask_empty_question():
    response = client.post("/ask", json={"question": ""})
    assert response.status_code == 422


def test_ask_whitespace_question():
    response = client.post("/ask", json={"question": "   "})
    assert response.status_code == 400


def test_ask_question_too_long():
    response = client.post("/ask", json={"question": "a" * 2001})
    assert response.status_code == 422


def test_ask_success(monkeypatch):
    monkeypatch.setattr(
        main,
        "rag_answer",
        lambda question: {
            "answer": "Machine learning is a subset of AI. [Source ID: 1]",
            "sources": [{"filename": "sample.pdf", "page": 2}]
        }
    )

    response = client.post(
        "/ask",
        json={"question": "  What is machine learning?  "}
    )

    assert response.status_code == 200
    assert response.json()["question"] == "What is machine learning?"
    assert len(response.json()["sources"]) == 1


def test_ask_server_error(monkeypatch):
    def failing_answer(question):
        raise RuntimeError("Simulated failure")

    monkeypatch.setattr(main, "rag_answer", failing_answer)

    response = client.post(
        "/ask",
        json={"question": "What is AI?"}
    )

    assert response.status_code == 500


def test_upload_invalid_file():
    response = client.post(
        "/documents/upload",
        files={"file": ("test.txt", b"Test content", "text/plain")}
    )
    assert response.status_code == 400


def test_upload_empty_file():
    response = client.post(
        "/documents/upload",
        files={"file": ("empty.pdf", b"", "application/pdf")}
    )
    assert response.status_code == 400


def test_upload_too_large(monkeypatch):
    monkeypatch.setattr(main, "MAX_FILE_SIZE", 10)

    response = client.post(
        "/documents/upload",
        files={"file": ("large.pdf", b"x" * 11, "application/pdf")}
    )

    assert response.status_code == 413


def test_upload_success(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path)

    monkeypatch.setattr(
        main,
        "process_document",
        lambda **kwargs: {"chunks_created": 3}
    )

    content = b"Fake PDF content for an isolated API test."

    response = client.post(
        "/documents/upload",
        files={"file": ("sample.pdf", content, "application/pdf")}
    )

    assert response.status_code == 200
    assert response.json()["filename"] == "sample.pdf"
    assert response.json()["processing"]["chunks_created"] == 3
    assert len(list(tmp_path.iterdir())) == 1


def test_upload_duplicate_file(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path)

    content = b"Duplicate test content."
    file_hash = hashlib.sha256(content).hexdigest()

    existing_file = tmp_path / f"{file_hash}_sample.pdf"
    existing_file.write_bytes(content)

    response = client.post(
        "/documents/upload",
        files={"file": ("sample.pdf", content, "application/pdf")}
    )

    assert response.status_code == 409


def test_upload_processing_validation_error(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path)

    def invalid_document(**kwargs):
        raise ValueError("No readable text found in document.")

    monkeypatch.setattr(main, "process_document", invalid_document)

    response = client.post(
        "/documents/upload",
        files={"file": ("invalid.pdf", b"Fake PDF content", "application/pdf")}
    )

    assert response.status_code == 422
    assert len(list(tmp_path.iterdir())) == 0


def test_upload_processing_server_error(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path)

    def failing_processor(**kwargs):
        raise RuntimeError("Simulated processing failure")

    monkeypatch.setattr(main, "process_document", failing_processor)

    response = client.post(
        "/documents/upload",
        files={"file": ("broken.pdf", b"Fake PDF content", "application/pdf")}
    )

    assert response.status_code == 500
    assert len(list(tmp_path.iterdir())) == 0


def test_delete_document_success(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path)

    file_hash = "testhash123"
    uploaded_file = tmp_path / f"{file_hash}_sample.pdf"
    uploaded_file.write_bytes(b"Test content")

    class FakeCollection:
        def __init__(self):
            self.deleted = False

        def get(self, **kwargs):
            return {"ids": ["chunk1", "chunk2"]}

        def delete(self, **kwargs):
            self.deleted = True

    fake_collection = FakeCollection()
    monkeypatch.setattr(main, "collection", fake_collection)

    response = client.delete(f"/documents/{file_hash}")

    assert response.status_code == 200
    assert response.json()["deleted_chunks"] == 2
    assert fake_collection.deleted is True
    assert not uploaded_file.exists()


def test_delete_document_not_found(monkeypatch):
    class FakeCollection:
        def get(self, **kwargs):
            return {"ids": []}

    monkeypatch.setattr(main, "collection", FakeCollection())

    response = client.delete("/documents/unknownhash")

    assert response.status_code == 404
