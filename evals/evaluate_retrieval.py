
import json
import sys
from pathlib import Path
from collections import defaultdict

# Make the project root importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.ingestion.processor import collection, embedding_model


# -----------------------------
# Configuration
# -----------------------------

DATASET_PATH = PROJECT_ROOT / "evals" / "golden_questions.json"
RESULTS_DIR = PROJECT_ROOT / "evals" / "results"

K_VALUES = [2, 4, 6]

# Retrieve extra candidates because the database contains
# duplicate chunks. We evaluate unique filename/page pairs.
CANDIDATE_POOL = 100


# -----------------------------
# Load golden questions
# -----------------------------

with open(DATASET_PATH, "r", encoding="utf-8") as file:
    questions = json.load(file)

answerable_questions = [
    item for item in questions
    if item["category"] == "answerable"
]


# -----------------------------
# Retrieve relevant source pages
# -----------------------------

def retrieve_source_pages(question, n_results):
    query_embedding = embedding_model.encode([question]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(n_results, collection.count()),
        include=["metadatas", "distances"]
    )

    retrieved_pages = []
    seen_pages = set()

    metadatas = results["metadatas"][0]

    for metadata in metadatas:
        if not metadata:
            continue

        filename = metadata.get("filename")
        page = metadata.get("page")

        if filename is None or page is None:
            continue

        source = (filename, page)

        # Count each source page only once
        if source not in seen_pages:
            seen_pages.add(source)
            retrieved_pages.append(source)

    return retrieved_pages


# -----------------------------
# Evaluation metrics
# -----------------------------

def evaluate_at_k(k):
    hit_count = 0
    recall_scores = []
    reciprocal_ranks = []

    for item in answerable_questions:
        question = item["question"]

        relevant_sources = {
            (source["filename"], source["page"])
            for source in item["relevant_sources"]
        }

        retrieved_pages = retrieve_source_pages(
            question,
            CANDIDATE_POOL
        )

        top_k = retrieved_pages[:k]

        # Hit Rate: did we retrieve at least one relevant page?
        relevant_retrieved = [
            page for page in top_k
            if page in relevant_sources
        ]

        if relevant_retrieved:
            hit_count += 1

        # Recall: what proportion of relevant pages did we retrieve?
        recall = len(set(relevant_retrieved)) / len(relevant_sources)
        recall_scores.append(recall)

        # MRR: reciprocal rank of the first relevant page
        reciprocal_rank = 0

        for rank, page in enumerate(top_k, start=1):
            if page in relevant_sources:
                reciprocal_rank = 1 / rank
                break

        reciprocal_ranks.append(reciprocal_rank)

    total = len(answerable_questions)

    return {
        "k": k,
        "hit_rate": hit_count / total,
        "recall": sum(recall_scores) / total,
        "mrr": sum(reciprocal_ranks) / total,
        "evaluated_questions": total
    }


# -----------------------------
# Run evaluation
# -----------------------------

def main():
    print("=" * 55)
    print("RETRIEVAL EVALUATION")
    print("=" * 55)

    print(f"Total golden questions: {len(questions)}")
    print(f"Answerable questions: {len(answerable_questions)}")
    print(f"Unanswerable questions excluded: "
          f"{len(questions) - len(answerable_questions)}")

    results = []

    for k in K_VALUES:
        metrics = evaluate_at_k(k)
        results.append(metrics)

        print(f"\nMetrics at K={k}")
        print(f"Hit Rate@{k}: {metrics['hit_rate']:.4f}")
        print(f"Recall@{k}:   {metrics['recall']:.4f}")
        print(f"MRR:          {metrics['mrr']:.4f}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    output_path = RESULTS_DIR / "retrieval_metrics.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(results, file, indent=4)

    print("\nResults saved to:")
    print(output_path)


if __name__ == "__main__":
    main()
