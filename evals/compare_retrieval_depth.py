
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.rag.service import retrieve_documents

dataset_path = PROJECT_ROOT / "evals" / "golden_questions.json"

with open(dataset_path, "r", encoding="utf-8") as file:
    questions = json.load(file)

for k in [4, 6]:
    answerable_total = 0
    answerable_retrieved = 0
    unanswerable_total = 0
    unanswerable_rejected = 0

    print(f"\n{'=' * 55}")
    print(f"RETRIEVAL DEPTH: k={k}")
    print(f"{'=' * 55}")

    for item in questions:
        retrieved = retrieve_documents(item["question"], k=k)

        best_distance = (
            min(source["distance"] for source in retrieved)
            if retrieved else float("inf")
        )

        relevant_found = any(
            source["filename"] == expected["filename"]
            and source["page"] == expected["page"]
            for source in retrieved
            for expected in item["relevant_sources"]
        )

        admitted = best_distance <= 0.50

        if item["relevant_sources"]:
            answerable_total += 1

            if relevant_found and admitted:
                answerable_retrieved += 1
            else:
                print(
                    f"ANSWERABLE ISSUE {item['id']}: "
                    f"distance={best_distance:.4f}, "
                    f"relevant_found={relevant_found}"
                )
        else:
            unanswerable_total += 1

            if not admitted:
                unanswerable_rejected += 1
            else:
                print(
                    f"UNANSWERABLE ACCEPTED {item['id']}: "
                    f"distance={best_distance:.4f}"
                )

    print(
        f"\nAnswerable with relevant source admitted: "
        f"{answerable_retrieved}/{answerable_total}"
    )
    print(
        f"Unanswerable correctly rejected: "
        f"{unanswerable_rejected}/{unanswerable_total}"
    )

print("\nRetrieval-depth comparison completed.")
