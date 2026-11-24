
import json
import re
import shutil
from pathlib import Path

results_path = Path("evals/results/answer_evaluation.json")
gold_path = Path("evals/golden_questions.json")
backup_path = Path("evals/results/answer_evaluation_before_repair.json")

# Preserve the original evaluation results
shutil.copy2(results_path, backup_path)

with open(results_path, encoding="utf-8") as f:
    results = json.load(f)

with open(gold_path, encoding="utf-8") as f:
    golden_questions = json.load(f)

gold_by_id = {item["id"]: item for item in golden_questions}

repaired = 0

for result in results:
    # Preserve records where Gemini returned an API error
    if "error" in result or "generated_answer" not in result:
        continue

    answer = result.get("generated_answer", "")
    sources = result.get("returned_sources", [])

    # Extract all source IDs, including combined citations
    cited_ids = re.findall(r"Source ID:\s*(\d+)", answer)

    valid_ids = set(range(1, len(sources) + 1))
    parsed_ids = [int(source_id) for source_id in cited_ids]

    valid_citations = (
        len(parsed_ids) > 0
        and all(source_id in valid_ids for source_id in parsed_ids)
    )

    cited_sources = [
        sources[source_id - 1]
        for source_id in parsed_ids
        if source_id in valid_ids
    ]

    result["cited_sources"] = cited_sources
    result["has_citation"] = len(parsed_ids) > 0
    result["valid_citations"] = valid_citations

    if result["category"] == "unanswerable":
        result["relevant_citation"] = None
    else:
        gold = gold_by_id[result["id"]]
        expected_sources = gold["relevant_sources"]

        result["relevant_citation"] = any(
            cited["filename"] == expected["filename"]
            and cited["page"] == expected["page"]
            for cited in cited_sources
            for expected in expected_sources
        )

    repaired += 1

with open(results_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("Citation repair completed.")
print("Records repaired:", repaired)
print("Backup:", backup_path)
