
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.rag.service import retrieve_documents

dataset_path = PROJECT_ROOT / "evals" / "golden_questions.json"

with open(dataset_path, "r", encoding="utf-8") as file:
    questions = json.load(file)

thresholds = [0.50, 0.60]

results = []

for item in questions:
    question = item["question"]
    expected_sources = item["relevant_sources"]

    retrieved = retrieve_documents(question, k=4)

    best_distance = (
        min(source["distance"] for source in retrieved)
        if retrieved else float("inf")
    )

    relevant_found = any(
        source["filename"] == expected["filename"]
        and source["page"] == expected["page"]
        for source in retrieved
        for expected in expected_sources
    )

    results.append({
        "id": item["id"],
        "question": question,
        "answerable": bool(expected_sources),
        "best_distance": best_distance,
        "relevant_found": relevant_found,
    })

for threshold in thresholds:
    answerable = [r for r in results if r["answerable"]]
    unanswerable = [r for r in results if not r["answerable"]]

    answerable_retrieved = sum(
        r["relevant_found"] and r["best_distance"] <= threshold
        for r in answerable
    )

    unanswerable_rejected = sum(
        r["best_distance"] > threshold
        for r in unanswerable
    )

    print(f"\n{'=' * 55}")
    print(f"THRESHOLD: {threshold:.2f}")
    print(f"{'=' * 55}")

    print(
        f"Answerable questions with relevant source admitted: "
        f"{answerable_retrieved}/{len(answerable)}"
    )

    print(
        f"Unanswerable questions correctly rejected: "
        f"{unanswerable_rejected}/{len(unanswerable)}"
    )

    print("\nQuestions affected by this threshold:")

    for result in results:
        admitted = result["best_distance"] <= threshold

        if result["answerable"] and (
            not admitted or not result["relevant_found"]
        ):
            print(
                f"  {result['id']}: ANSWERABLE ISSUE | "
                f"distance={result['best_distance']:.4f} | "
                f"relevant_found={result['relevant_found']}"
            )

        elif not result["answerable"] and admitted:
            print(
                f"  {result['id']}: UNANSWERABLE ACCEPTED | "
                f"distance={result['best_distance']:.4f}"
            )

print("\nComparison completed.")
