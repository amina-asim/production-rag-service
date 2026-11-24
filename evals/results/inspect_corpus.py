
import sys
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from app.ingestion.processor import collection

result = collection.get(include=["documents", "metadatas"])
grouped = defaultdict(list)

for chunk_id, text, metadata in zip(
    result["ids"], result["documents"], result["metadatas"]
):
    filename = metadata.get("filename", "Unknown")
    text = text or ""

    # Exclude very short or mostly non-text chunks
    if len(text) < 500:
        continue

    alphabetic = sum(character.isalpha() for character in text)
    if alphabetic < 300:
        continue

    lower_text = text.lower()
    if any(term in lower_text[:150] for term in [
        "table of contents", "acknowledgments", "acknowledgements"
    ]):
        continue

    grouped[filename].append({
        "chunk_id": chunk_id,
        "page": metadata.get("page", 0),
        "chunk_position": metadata.get("chunk_position", -1),
        "text": text
    })

report = [
    "QUALITY-FILTERED CORPUS SAMPLES",
    f"Total indexed chunks: {len(result['documents'])}"
]

for filename, chunks in sorted(grouped.items()):
    chunks.sort(key=lambda x: (int(x["page"]), x["chunk_position"]))

    report.extend([
        "\n" + "=" * 60,
        f"DOCUMENT: {filename}",
        f"QUALIFYING CHUNKS: {len(chunks)}"
    ])

    if not chunks:
        report.append("No qualifying chunks found.")
        continue

    # Select up to 8 chunks distributed across the document
    count = min(8, len(chunks))
    indices = [
        round(i * (len(chunks) - 1) / max(count - 1, 1))
        for i in range(count)
    ]

    for index in indices:
        chunk = chunks[index]
        report.extend([
            "\n" + "-" * 60,
            f"CHUNK ID: {chunk['chunk_id']}",
            f"PAGE: {chunk['page']}",
            f"CHUNK POSITION: {chunk['chunk_position']}",
            "-" * 60,
            chunk["text"][:1200]
        ])

output_path = Path(__file__).parent / "quality_samples.txt"
output_path.write_text("\n".join(report), encoding="utf-8")

print("Filtered samples saved to:")
print(output_path)
print(f"Documents inspected: {len(grouped)}")
