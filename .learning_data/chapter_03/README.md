# Chapter 3 — Local IT Support Knowledge Assistant

This exercise turns RAG into a small, realistic IT help-desk knowledge assistant.

## Why this dataset?

`knowledge_base.json` contains 8 short, structured support articles covering network connectivity, DNS, printers, disk space, application crashes, phishing, and local Ollama troubleshooting. The articles are concise enough for a laptop but rich enough to create multiple chunks and test similar symptoms across topics.

`knowledge_base.txt` is the same content in a readable text format. The Python script uses the JSON file so it can preserve article IDs, categories, titles, and source URLs as metadata.

The articles are original concise summaries with links to official documentation for further reading. Treat them as a learning dataset, not as a replacement for current vendor guidance.

## Models you already have

Based on your `ollama list` output, use:

- Embeddings: `nomic-embed-text`
- Answer generation: `qwen2.5:3b`

These have separate jobs. The embedding model turns text and questions into vectors. The Qwen model writes the final answer from retrieved context.

## 1. Install the Python integrations

From the repository root, using your existing virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -U langchain-chroma langchain-ollama langchain-text-splitters
```

No Hugging Face token is needed for this chapter because the embedding model is served locally by Ollama.

## 2. Check Ollama models

```powershell
ollama list
ollama run nomic-embed-text "DNS troubleshooting"
```

If the second command is not supported by your Ollama CLI version, simply confirm the model is listed and continue. The Python application will request embeddings through Ollama.

Make sure Ollama is running before starting the script.

## 3. Run the evaluator

From the repository root:

```powershell
.\.venv\Scripts\python.exe .\.learning_data\chapter_03\evaluate_rag.py
```

If your launcher uses the current environment already, this may also work:

```powershell
python .\.learning_data\chapter_03\evaluate_rag.py
```

## 4. What the code does

1. Loads the eight articles from JSON.
2. Converts each article into a LangChain `Document`, preserving article metadata.
3. Splits documents into 650-character chunks with 100-character overlap.
4. Creates or reuses a local Chroma index with cosine distance.
5. Retrieves the top three chunks for each test question.
6. Compares the best cosine distance to a configurable threshold.
7. Generates an answer with `qwen2.5:3b` only when the retrieval result passes the threshold.
8. Reports whether each in-scope/out-of-scope decision matched the expected result.

The index is saved under `eval_store/`. A fingerprint checks the source data and chunk/model configuration. If they change, the index is rebuilt; otherwise the saved index is reused.

## 5. Important: calibrate the threshold

A distance score is not a universal confidence percentage. Lower cosine distance means closer vectors, but the useful threshold depends on the embedding model, data, chunking, and question.

The default threshold is `0.55`. Treat it as a starting point, not a guaranteed correct value. Inspect the scores printed by your run. If relevant questions are refused or unrelated questions are accepted, try a different threshold and rerun.

Set a temporary threshold in PowerShell:

```powershell
$env:RAG_DISTANCE_THRESHOLD = "0.65"
.\.venv\Scripts\python.exe .\.learning_data\chapter_03\evaluate_rag.py
```

Replace `0.65` with the value you want to test. Close the terminal or run `Remove-Item Env:RAG_DISTANCE_THRESHOLD` to remove the override.

## 6. Experiments

1. Change `CHUNK_SIZE` from 650 to 300. Compare chunk count and retrieved article.
2. Change `CHUNK_OVERLAP` from 100 to 0. Ask questions whose answer needs context from adjacent sentences.
3. Add a ninth article about a problem you know well. Ask one direct question and one paraphrased question about it.
4. Add a question about a topic absent from the knowledge base. Watch whether it is refused.
5. Try thresholds such as `0.40`, `0.55`, and `0.70`. Record false accepts and false refusals.
6. Temporarily change `GENERATION_MODEL` to `qwen2.5:1.5b` and compare answer quality and latency.
7. Compare the TXT file to the JSON. Understand why structured records and metadata help with provenance and evaluation.

## 7. Limitations to notice

- The evaluation's PASS/FAIL label checks the relevance/refusal decision. It does not prove the generated answer is factually correct.
- A single best-chunk threshold can reject a useful answer or accept an irrelevant one. Later, you can evaluate multiple retrieved chunks, reranking, and more robust abstention.
- The terminal demo sends one retrieved chunk to the LLM. Improving context assembly is a possible follow-up exercise.
- The sample contains a small number of articles, not a comprehensive support corpus.
- Do not run potentially destructive troubleshooting actions just because an LLM recommends them. This app only provides guidance; it does not execute commands.

## 8. Troubleshooting

### `Connection refused` or Ollama connection error
Start the Ollama Windows application/service and retry.

### `model not found`
Run `ollama list` and ensure both `nomic-embed-text` and `qwen2.5:3b` are present. Use the exact model names listed there.

### Import error for `langchain_ollama`
Install `langchain-ollama` into the same virtual environment used to run the script.

### Relevant questions are refused
Inspect the printed cosine distance. Try a higher threshold and check the top retrieved article. A high distance can also indicate poor chunking or a missing article.

### Unrelated questions are accepted
Try a lower threshold. Do not assume a threshold alone guarantees safe refusal; use evaluation cases and review the actual retrieved text.

## Completion checklist

- [ ] Script loads all eight articles.
- [ ] Chunk count is greater than the number of articles.
- [ ] Re-running without data/config changes reuses the saved index.
- [ ] Changing the source data or chunk settings rebuilds the index.
- [ ] Relevant and out-of-scope query distances are visible.
- [ ] Threshold behavior has been tested at several values.
- [ ] I can explain why retrieval PASS does not guarantee a correct generated answer.
