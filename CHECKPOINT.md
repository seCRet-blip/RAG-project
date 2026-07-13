# Checkpoint 1 — Data in Qdrant

You have completed the **data source → processing → vector store** pipeline.
Everything below is **free** (local crawl, local embeddings, local Qdrant).

## What is running (do not disturb)

| Container | Port | Network | Touch? |
|-----------|------|---------|--------|
| `live-retrain-dashboard` | **8787** | ai_sniper_bot | **Never** |
| `multi-asset-scheduler` | **8001** | ai_sniper_bot | **Never** |
| `auto-retrain-monitor` | — | ai_sniper_bot | **Never** |
| `rag-qdrant` | 6333–6334 | rag-project-net | RAG only |
| `rag-monthly-scheduler` | none | rag-project-net | RAG only |

RAG services use a **separate Docker network** (`rag-project-net`) and **no conflicting ports**.

## The pipeline you built

```
Crawl (kubernetes.io + docs.docker.com)
    ↓  data/raw/html/
Extract (title, headings, body)
    ↓  data/processed/extracted/
Clean (normalize text)
    ↓  data/processed/cleaned/
Chunk (split for retrieval)
    ↓  data/processed/chunks/*.jsonl
Index (local embeddings → Qdrant)
    ↓  collection: documents
```

## Commands to follow along

### 1. Check sync status
```powershell
type data\sync_checkpoint.json
```

### 2. Inspect raw crawl
```powershell
type data\raw\kubernetes_manifest.json
type data\raw\docker_manifest.json
```

### 3. Inspect one extracted doc
```powershell
type data\processed\extracted\docker\docs.docker.com__reference__dockerfile.json
```

### 4. Inspect one cleaned doc
```powershell
type data\processed\cleaned\docker\docs.docker.com__reference__dockerfile.json
```

### 5. Preview chunks
```powershell
py -m scripts.inspect_chunks --source docker --search ENTRYPOINT --limit 2
py -m scripts.inspect_chunks --source kubernetes --search networking --limit 2
```

### 6. Verify Qdrant has data (free, browser)
Open: http://127.0.0.1:6333/dashboard

Collection name: `documents`

### 7. Re-run full sync manually
```powershell
py -m scripts.sync_docs
```

### 8. Re-index without re-crawling
```powershell
py -m scripts.sync_docs --skip-crawl
```

## Monthly auto-refresh

**Docker (recommended on your machine):**
```powershell
docker compose -f docker-compose.crawler.yml up -d monthly-scheduler
```

Runs on the **1st of each month at 03:00 UTC**:
1. Crawl kubernetes + docker docs
2. Process (extract → clean → chunk)
3. Recreate Qdrant collection and re-index

**Kubernetes:**
```bash
kubectl apply -f k8s/crawler-cronjob.yaml
```

## Files to read in order (learning path)

1. `crawler/config.py` — seed URLs and limits
2. `crawler/crawl.py` — BFS crawler
3. `processing/extract.py` — HTML → JSON
4. `processing/clean.py` — text normalization
5. `processing/chunk.py` — chunking strategy
6. `scripts/sync_docs.py` — ties it all together
7. `retriever/chunk_loader.py` — embeddings → Qdrant

## Next checkpoint (when you are ready)

**Checkpoint 2 is ready** — see [CHECKPOINT2.md](CHECKPOINT2.md) for retrieval + chat setup.

## Cost summary

| Step | Tool | Cost |
|------|------|------|
| Crawl | httpx + BeautifulSoup | $0 |
| Embeddings | fastembed (local ONNX) | $0 |
| Vector DB | Qdrant (local Docker) | $0 |
| LLM | vLLM (local, optional) | $0 |
