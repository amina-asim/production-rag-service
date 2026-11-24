

\# Production RAG Service



A document-based Retrieval-Augmented Generation (RAG) application that allows users to upload PDF and DOCX files and ask questions about their contents.



The system retrieves relevant document passages, generates grounded answers using Google Gemini, and provides source citations.



\## Features



\- PDF and DOCX document ingestion

\- SHA-256 duplicate document detection

\- Text extraction and chunking

\- Semantic search using Sentence Transformers

\- Persistent vector storage with ChromaDB

\- Context-grounded question answering using Google Gemini

\- Source citations in generated answers

\- Refusal when relevant evidence is unavailable

\- Document listing and deletion

\- FastAPI backend with Swagger documentation

\- Automated API tests using pytest

\- Retrieval and answer evaluation scripts



\*\*Interface:\*\* FastAPI Swagger UI is available at `/docs`. A separate HTML/CSS frontend is not yet implemented.



\## Technology Stack



| Component | Technology |

|---|---|

| Backend | FastAPI |

| Language | Python 3.11 |

| Embeddings | all-MiniLM-L6-v2 |

| Vector Database | ChromaDB |

| LLM | Google Gemini |

| PDF Processing | pypdf |

| DOCX Processing | python-docx |

| Text Chunking | LangChain Text Splitters |

| Testing | pytest, FastAPI TestClient |



\## Project Structure

production-rag-service/

├── app/

│   ├── main.py

│   ├── ingestion/

│   │   └── processor.py

│   └── rag/

│       └── service.py

├── data/

├── evals/

│   ├── golden\_questions.json

│   ├── evaluate\_retrieval.py

│   ├── evaluate\_answers.py

│   ├── compare\_retrieval\_depth.py

│   ├── compare\_thresholds.py

│   └── results/

├── notebooks/

├── frontend/

├── tests/

├── .env.example

├── .gitignore

├── AI\_USAGE.md

├── DESIGN.md

├── EVAL.md

├── README.md

└── requirements.txt

\## Installation



\### 1. Clone the repository



```bash

git clone YOUR\_GITHUB\_REPOSITORY\_URL

cd production-rag-service

```



\### 2. Create a virtual environment



```bash

python -m venv venv

```



Activate it on Windows:



```bash

venv\\Scripts\\activate

```



\### 3. Install dependencies



```bash

pip install -r requirements.txt

```



\### 4. Configure environment variables



Create a `.env` file in the project root using `.env.example` as a template.



```env

GEMINI\_API\_KEY=your\_gemini\_api\_key\_here

DISTANCE\_THRESHOLD=0.50

```



Never commit your actual API key.



\## Running the Application



Start the FastAPI server:



```bash

uvicorn app.main:app --reload

```



The API will be available at:



\- Application: http://127.0.0.1:8000

\- Swagger documentation: http://127.0.0.1:8000/docs

\- Health check: http://127.0.0.1:8000/health



\## API Endpoints



| Method | Endpoint | Description |

|---|---|---|

| GET | `/` | Check service status |

| GET | `/health` | Health check |

| POST | `/documents/upload` | Upload a PDF or DOCX |

| GET | `/documents` | List indexed documents |

| DELETE | `/documents/{file\_hash}` | Delete a document |

| POST | `/ask` | Ask a question |



\### Example question request



```json

{

&#x20; "question": "What is machine learning?"

}

```



\### Example response



```json

{

&#x20; "question": "What is machine learning?",

&#x20; "answer": "Answer grounded in retrieved documents \[Source ID: 1]",

&#x20; "sources": \[

&#x20;   {

&#x20;     "filename": "sample.pdf",

&#x20;     "page": 2

&#x20;   }

&#x20; ]

}

```



\## Running Tests



Execute the API test suite:



```bash

python -m pytest tests -v

```



The current test suite contains 17 passing tests covering API validation, document upload, duplicate detection, deletion, question answering and error handling.



\## Evaluation



The evaluation dataset contains 25 golden questions:



\- 20 answerable questions

\- 5 unanswerable questions



Retrieval metrics include Hit Rate@K, Recall@K and Mean Reciprocal Rank.



Detailed evaluation results, configuration comparisons and limitations are documented in \[EVAL.md](EVAL.md).



\## System Architecture



See \[DESIGN.md](DESIGN.md) for the ingestion pipeline, retrieval architecture, answer generation, citation validation and API design.



\## Configuration



Current production configuration:



| Setting | Value |

|---|---|

| Embedding model | all-MiniLM-L6-v2 |

| Vector database | ChromaDB |

| Similarity metric | Cosine |

| Chunk size | 800 |

| Chunk overlap | 150 |

| Retrieval depth | 4 |

| Distance threshold | 0.50 |

| LLM | Google Gemini |



\## Security Notes



\- API keys are stored in environment variables.

\- `.env` is excluded from Git.

\- Uploaded file extensions and file sizes are validated.

\- Duplicate files are detected using SHA-256 hashes.

\- Document processing failures trigger uploaded-file cleanup.



\## Future Improvements



\- Hybrid retrieval and reranking

\- Authentication and authorization

\- Improved frontend experience

\- Automated faithfulness evaluation

\- Monitoring and deployment

\- Additional document formats



\## AI Usage Disclosure



AI assistance was used during development for learning, debugging, implementation guidance, documentation and evaluation design.



The project uses Google Gemini for grounded answer generation. Development assistance and model usage should be documented with the actual tools, models and prompts used.



\## License



Add an appropriate license before public distribution.

```



Save and close Notepad.



\*\*One important note:\*\* The README includes a project structure based on the files we've discussed. We'll verify it against your actual folders before the first commit.



Run:



```cmd id="d9p8vv"

dir README.md

```



Tell me when saved.

