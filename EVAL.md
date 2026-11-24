# RAG System Evaluation

## 1. Evaluation Overview

The RAG system was evaluated using a golden dataset of 25 questions designed to measure retrieval quality, answer generation, citation validity, and refusal behavior.

The dataset contains:
- 20 answerable questions.
- 5 unanswerable questions.
- Reworded questions.
- Questions requiring information from multiple passages.
- Questions covering all three uploaded PDF documents.

## 2. Evaluation Dataset

The evaluation dataset is stored in:

`evals/golden_questions.json`

Each question includes:
- Question ID and category.
- Question text.
- Expected answer.
- Relevant document filename and page references.

Unanswerable questions have no relevant source references and are used to test whether the system correctly refuses unsupported questions.

## 3. Retrieval Evaluation

Retrieval was evaluated using Hit Rate@K, Recall@K, and Mean Reciprocal Rank (MRR).

### Results

| Metric | K=2 | K=4 | K=6 |
|---|---:|---:|---:|
| Hit Rate@K | 0.6000 | 0.8500 | 0.9000 |
| Recall@K | 0.5750 | 0.8500 | 0.9000 |
| MRR | 0.5250 | 0.6042 | 0.6142 |

The results indicate that retrieval quality improves as more candidate pages are considered.

K=4 was selected as the production retrieval setting to balance retrieval quality and the amount of context supplied to the language model.

The retrieval evaluation script is:

`evals/evaluate_retrieval.py`

Results are saved in:

`evals/results/retrieval_metrics.json`

### Metric Definitions

- **Hit Rate@K:** Proportion of answerable questions for which at least one relevant page appears in the top K results.
- **Recall@K:** Average proportion of relevant pages retrieved within the top K results.
- **MRR:** Average reciprocal rank of the first relevant result.

Unanswerable questions are excluded from these retrieval metrics.

## 4. Answer Generation Evaluation

Answer generation was evaluated using the RAG pipeline and the golden question dataset.

### Results

| Evaluation measure | Result |
|---|---:|
| Successfully evaluated | 23/25 |
| Answerable questions with relevant citations | 14/18 |
| Unanswerable questions correctly refused | 5/5 |

Two answer-generation requests encountered temporary Gemini API HTTP 503 errors. These were recorded as API errors and excluded from the successfully evaluated answerable questions.

The five unanswerable questions were correctly refused.

### Citation Validation

The evaluation checks:
- Whether an answer contains citations.
- Whether cited source IDs exist in the retrieved context.
- Whether at least one cited source matches the expected relevant document and page.

Citation validity does not independently prove that every individual factual claim is supported. Manual faithfulness review is also necessary.

The answer evaluation script is:

`evals/evaluate_answers.py`

Detailed results are saved in:

`evals/results/answer_evaluation.json`

## 5. Configuration Comparisons

### Retrieval Depth

Two production retrieval depths were compared:

- K=4
- K=6

The production retrieval-depth diagnostic found:

| Measure | K=4 | K=6 |
|---|---:|---:|
| Answerable questions with relevant source admitted | 15/20 | 15/20 |
| Unanswerable questions correctly rejected | 5/5 | 5/5 |

Increasing retrieval depth did not improve the number of answerable questions admitted under the current distance threshold.

Therefore, K=4 was retained.

The broader retrieval ranking evaluation separately showed improved Hit Rate@6 and Recall@6. The two evaluations measure different stages: ranked page retrieval and production evidence admission.

### Distance Threshold

The production distance threshold was compared at 0.50 and 0.60.

The 0.50 threshold correctly rejected all five unanswerable questions in the diagnostic run. At 0.60, one unanswerable question was admitted.

The 0.50 threshold was therefore retained to prioritize grounded answers and safe refusal behavior.

The threshold is configurable through the `DISTANCE_THRESHOLD` environment variable.

## 6. Production Configuration

The selected configuration is:

| Setting | Value |
|---|---|
| Embedding model | all-MiniLM-L6-v2 |
| Vector database | ChromaDB |
| Distance metric | Cosine |
| Retrieval depth | 4 pages |
| Distance threshold | 0.50 |
| Generation model | Gemini |
| Chunk size | 800 |
| Chunk overlap | 150 |
| Maximum question length | 2000 characters |

The retriever uses page-level context expansion to combine relevant chunks from a retrieved page before passing the context to the language model.

## 7. Known Limitations

The evaluation identified several limitations:

1. Some answerable questions were refused because their relevant evidence was not retrieved within the configured distance threshold.
2. Semantic retrieval does not consistently rank every relevant passage highly.
3. Increasing retrieval depth did not resolve all difficult retrieval cases.
4. Gemini API availability can affect evaluation runs through temporary HTTP 503 errors.
5. Valid citations do not guarantee complete factual faithfulness.
6. The golden dataset contains only 25 questions and is not large enough to represent every possible user query.

These limitations are documented rather than hidden by weakening the refusal behavior.

## 8. Reproducibility

Run the evaluation scripts from the project root with the virtual environment activated:

```bash
python evals/evaluate_retrieval.py
python evals/evaluate_answers.py
```

The evaluation results are stored under:

`evals/results/`

The Gemini API key must be configured in the local `.env` file. API keys must never be committed to GitHub.

## 9. Conclusion

The implemented RAG system demonstrates document ingestion, semantic retrieval, context construction, grounded answer generation, citation validation, and refusal of unsupported questions.

The retrieval evaluation achieved an 85% Hit Rate@4 and 85% Recall@4. The answer evaluation produced relevant citations for 14 of 18 successfully evaluated answerable questions and correctly refused all five unanswerable questions.

The system is functional, measurable, and reproducible, with identified limitations that provide clear opportunities for future improvement.
## 10. Manual Faithfulness Review

Five representative generated answers were manually reviewed against their retrieved document context.

| Question | Topic | Result |
|---|---|---|
| Q3 | L1 regularization | Pass |
| Q8 | CNN applications | Pass |
| Q10 | Healthcare AI | Pass |
| Q18 | AI and ML awareness | Pass |
| Q20 | AI usage and trust | Pass |

The reviewed answers were factually consistent with their cited document passages. Minor repetition was observed in the survey summary response.

This review is qualitative and covers five representative answers rather than the entire evaluation dataset.