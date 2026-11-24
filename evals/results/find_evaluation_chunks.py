
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from app.ingestion.processor import collection
from app.ingestion.processor import embedding_model

topics = [
    "supervised learning and unsupervised learning differences",
    "reinforcement learning and how it works",
    "convolutional neural network convolution pooling and filters",
    "recurrent neural networks and long short term memory",
    "multilayer perceptron XOR function",
    "overfitting underfitting and generalization",
    "dropout regularization in neural networks",
    "L1 and L2 regularization differences",
    "parameter norm penalties weight decay",
    "capsule networks architecture and advantages",
    "artificial intelligence healthcare finance education applications",
    "AI awareness machine learning awareness survey percentages",
    "trust in artificial intelligence decisions survey",
    "primary and secondary research methodology",
    "machine learning definition and learning from data"
]


for topic in topics:
    print("\n" + "=" * 75)
    print("TOPIC:", topic)
    print("=" * 75)

    #query_embedding = embedding_model.encode([topic]).tolist() if False else None
    query_embedding = embedding_model.encode([topic]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=10,
        include=["documents", "metadatas", "distances"]
    )

    
    seen = set()
    printed = 0

    for i, text in enumerate(results["documents"][0]):
        metadata = results["metadatas"][0][i]
        chunk_id = results["ids"][0][i]

        if not text or len(text) < 400:
            continue

        if text.strip() in seen:
            continue

        seen.add(text.strip())

        alphabetic = sum(c.isalpha() for c in text)
        if alphabetic < 250:
            continue

        print("\nCHUNK ID:", chunk_id)
        print("FILE:", metadata.get("filename"))
        print("PAGE:", metadata.get("page"))
        print("DISTANCE:", round(results["distances"][0][i], 4))
        print("TEXT:", text[:900])

        printed += 1

        if printed == 3:
            break
