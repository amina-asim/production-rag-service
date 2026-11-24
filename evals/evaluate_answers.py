
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.rag.service import rag_answer


DATASET_PATH = PROJECT_ROOT / "evals" / "golden_questions.json"
RESULTS_DIR = PROJECT_ROOT / "evals" / "results"

REFUSAL_TEXT = (
    "I could not find relevant information in the uploaded documents."
)

# Use the working retrieval configuration
K = 4


def is_refusal(answer):
    return (
        REFUSAL_TEXT.lower() in answer.lower()
        or "could not provide a properly cited answer" in answer.lower()
    )


def evaluate_question(item):
    question = item["question"]

    # Generate an answer using the existing RAG pipeline
    result = rag_answer(question, k=K)

    answer = result["answer"]
    sources = result["sources"]

    # Find citation IDs in the generated answer
    cited_ids = [
        int(value)
        for value in re.findall(r"Source ID:\s*(\d+)", answer)
    ]

    # Check whether all cited IDs refer to returned sources
    valid_citations = (
        len(cited_ids) > 0
        and all(1 <= source_id <= len(sources) for source_id in cited_ids)
    )

    # Map cited IDs to their actual source pages
    cited_sources = []

    for source_id in sorted(set(cited_ids)):
        if 1 <= source_id <= len(sources):
            source = sources[source_id - 1]
            cited_sources.append({
                "filename": source["filename"],
                "page": source["page"]
            })

    relevant_sources = {
        (source["filename"], source["page"])
        for source in item["relevant_sources"]
    }

    cited_source_pairs = {
        (source["filename"], source["page"])
        for source in cited_sources
    }

    # For answerable questions, check whether a cited page
    # matches at least one expected relevant source.
    relevant_citation = (
        bool(cited_source_pairs & relevant_sources)
        if item["category"] == "answerable"
        else None
    )

    refused = is_refusal(answer)

    return {
        "id": item["id"],
        "category": item["category"],
        "question": question,
        "expected_answer": item["expected_answer"],
        "generated_answer": answer,
        "returned_sources": sources,
        "cited_sources": cited_sources,
        "refused": refused,
        "has_citation": len(cited_ids) > 0,
        "valid_citations": valid_citations,
        "relevant_citation": relevant_citation,

        # These require human review; the script does not guess.
        "manual_correctness_score": None,
        "manual_faithfulness_score": None
    }


def main():
    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        questions = json.load(file)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    evaluated = []

    print("=" * 55)
    print("RAG ANSWER EVALUATION")
    print("=" * 55)
    print(f"Questions: {len(questions)}")
    print(f"Retrieval K: {K}")
    print("Generating answers. Please wait...\n")

    for index, item in enumerate(questions, start=1):
        print(f"[{index}/{len(questions)}] Evaluating {item['id']}")

        try:
            evaluation = evaluate_question(item)
            evaluated.append(evaluation)

            print(f"  Refused: {evaluation['refused']}")
            print(f"  Citation valid: {evaluation['valid_citations']}")
            print(f"  Relevant citation: {evaluation['relevant_citation']}")

        except Exception as error:
            print(f"  ERROR: {error}")

            evaluated.append({
                "id": item["id"],
                "category": item["category"],
                "question": item["question"],
                "error": str(error)
            })

    output_path = RESULTS_DIR / "answer_evaluation.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(evaluated, file, indent=4, ensure_ascii=False)

    successful = [
        item for item in evaluated
        if "error" not in item
    ]

    answerable = [
        item for item in successful
        if item["category"] == "answerable"
    ]

    unanswerable = [
        item for item in successful
        if item["category"] == "unanswerable"
    ]

    print("\n" + "=" * 55)
    print("EVALUATION SUMMARY")
    print("=" * 55)
    print(f"Successfully evaluated: {len(successful)}/{len(questions)}")

    if answerable:
        relevant = sum(
            item["relevant_citation"] is True
            for item in answerable
        )
        print(
            f"Answerable questions with relevant citations: "
            f"{relevant}/{len(answerable)}"
        )

    if unanswerable:
        refusals = sum(item["refused"] for item in unanswerable)
        print(
            f"Unanswerable questions correctly refused: "
            f"{refusals}/{len(unanswerable)}"
        )

    print(f"\nDetailed results saved to:\n{output_path}")


if __name__ == "__main__":
    main()
