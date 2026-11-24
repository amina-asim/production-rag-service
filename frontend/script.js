
const API_BASE = window.location.origin;

const fileInput = document.getElementById("file-input");
const uploadButton = document.getElementById("upload-button");
const uploadMessage = document.getElementById("upload-message");
const askButton = document.getElementById("ask-button");
const questionInput = document.getElementById("question-input");

const answerArea = document.getElementById("answer-area");
const answerText = document.getElementById("answer-text");
const sourcesArea = document.getElementById("sources-area");

const documentList = document.getElementById("document-list");
const connectionStatus = document.getElementById("connection-status");

const chatSection = document.getElementById("chat-section");
const librarySection = document.getElementById("library-section");


// Display safe text rather than interpreting document content as HTML.
function addText(parent, tag, value) {
    const element = document.createElement(tag);
    element.textContent = value ?? "";
    parent.appendChild(element);
    return element;
}


// 1. Check whether the backend is available.
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);

        if (!response.ok) {
            throw new Error("Health check failed");
        }

        connectionStatus.textContent = "API connected";
        connectionStatus.style.color = "#21966c";
    } catch (error) {
        connectionStatus.textContent = "API unavailable";
        connectionStatus.style.color = "#d64c5c";
    }
}


// 2. Upload a PDF or DOCX document.
async function uploadDocument() {
    const file = fileInput.files[0];

    if (!file) {
        uploadMessage.textContent = "Please select a PDF or DOCX file.";
        return;
    }

    const allowedExtensions = [".pdf", ".docx"];
    const extension = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();

    if (!allowedExtensions.includes(extension)) {
        uploadMessage.textContent = "Only PDF and DOCX files are supported.";
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    uploadButton.disabled = true;
    uploadButton.textContent = "Uploading...";
    uploadMessage.textContent = "";

    try {
        const response = await fetch(`${API_BASE}/documents/upload`, {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || "Document upload failed.");
        }

        uploadMessage.textContent =
            `Successfully uploaded ${result.filename}.`;

        fileInput.value = "";

        await loadDocuments();

    } catch (error) {
        uploadMessage.textContent = error.message;
    } finally {
        uploadButton.disabled = false;
        uploadButton.textContent = "＋ Upload file";
    }
}


// 3. Ask a question using the RAG API.
async function askQuestion() {
    const question = questionInput.value.trim();

    if (!question) {
        alert("Please enter a question first.");
        return;
    }

    askButton.disabled = true;
    askButton.textContent = "Thinking...";

    answerArea.classList.remove("hidden");
    answerText.textContent = "Searching your documents and generating an answer...";
    sourcesArea.replaceChildren();

    try {
        const response = await fetch(`${API_BASE}/ask`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ question })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || "Unable to answer this question.");
        }

        answerText.textContent = result.answer || "No answer was returned.";

        const sourcesHeading = addText(sourcesArea, "h4", "Retrieved Sources");

        if (Array.isArray(result.sources) && result.sources.length > 0) {
            result.sources.forEach((source, index) => {
                const card = document.createElement("div");
                card.className = "source-card";

                const filename = source.filename || "Unknown document";
                const page = source.page ?? "Unknown";
                const sourceId = source.source_id || source.id || `Source ${index + 1}`;

                addText(card, "strong", `${sourceId}`);
                addText(card, "p", `Document: ${filename}`);
                addText(card, "p", `Page: ${page}`);

                const excerpt = source.text || source.document;
                if (excerpt) {
                    addText(card, "p", excerpt);
                }

                sourcesArea.appendChild(card);
            });
        } else {
            sourcesHeading.textContent = "No source details returned.";
        }

    } catch (error) {
        answerText.textContent = `Error: ${error.message}`;
    } finally {
        askButton.disabled = false;
        askButton.textContent = "Ask question →";
    }
}


// 4. Retrieve the uploaded document list.
async function loadDocuments() {
    documentList.replaceChildren();
    addText(documentList, "p", "Loading documents...");

    try {
        const response = await fetch(`${API_BASE}/documents`);
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || "Could not load documents.");
        }

        documentList.replaceChildren();

        const documents = Array.isArray(result)
            ? result
            : (result.documents || []);

        if (documents.length === 0) {
            addText(documentList, "p", "No documents uploaded yet.");
            return;
        }

        
documents.forEach(doc => {
    const item = document.createElement("div");
    item.className = "document-item";

    const details = document.createElement("div");
    addText(details, "strong", doc.filename || "Unnamed document");
    addText(details, "p", `${doc.chunks_count ?? 0} chunks`);

    const deleteButton = document.createElement("button");
    deleteButton.className = "delete-button";
    deleteButton.textContent = "Delete";

    deleteButton.addEventListener("click", () => {
        deleteDocument(doc.file_hash, doc.filename);
    });

    item.appendChild(details);
    item.appendChild(deleteButton);
    documentList.appendChild(item);
});


    } catch (error) {
        documentList.replaceChildren();
        addText(documentList, "p", `Error: ${error.message}`);
    }
}


// 5. Delete a document from the backend.
async function deleteDocument(fileHash, filename) {
    if (!fileHash) {
        alert("This document does not have a deletable file hash.");
        return;
    }

    const confirmed = confirm(`Delete "${filename}" and its indexed content?`);

    if (!confirmed) {
        return;
    }

    try {
        const response = await fetch(
            `${API_BASE}/documents/${encodeURIComponent(fileHash)}`,
            { method: "DELETE" }
        );

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || "Document deletion failed.");
        }

        alert(`Deleted ${filename}.`);
        await loadDocuments();

    } catch (error) {
        alert(error.message);
    }
}


// 6. Switch between chat and document library.
document.getElementById("nav-chat").addEventListener("click", () => {
    chatSection.classList.remove("hidden");
    librarySection.classList.add("hidden");

    document.getElementById("nav-chat").classList.add("active");
    document.getElementById("nav-library").classList.remove("active");
});

document.getElementById("nav-library").addEventListener("click", () => {
    chatSection.classList.add("hidden");
    librarySection.classList.remove("hidden");

    document.getElementById("nav-library").classList.add("active");
    document.getElementById("nav-chat").classList.remove("active");

    loadDocuments();
});


// 7. Connect buttons to their functions.
uploadButton.addEventListener("click", uploadDocument);
askButton.addEventListener("click", askQuestion);

document.getElementById("refresh-button").addEventListener("click", loadDocuments);


// Initial setup.
checkHealth();
