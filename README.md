# Production-Grade Agentic RAG

An enterprise-style **Retrieval-Augmented Generation (RAG) API** built as a stateful, multi-node agent graph rather than a single prompt-and-retrieve call. The system routes queries through intent detection, guardrails, vector retrieval, semantic reranking, and LLM synthesis — with conversation memory, an LLM gateway (caching/fallback/retry), and a RAGAS-based evaluation harness for measuring answer quality.

The assistant is scoped to a specific enterprise-IT domain (Kubernetes, Intel hardware, and enterprise networking) and refuses off-topic or adversarial (jailbreak) queries via guardrails before any retrieval happens.

## Architecture

```
User Query
   │
   ▼
NeMo Guardrails (jailbreak / off-topic gate)
   │  blocked? → return canned refusal, skip pipeline
   ▼
LangGraph Agent
   │
   ├─ Planner Node ──────────► LLM classifies intent:
   │                            "CONVERSATIONAL" (use chat memory only)
   │                            or a refined technical search query
   │
   ├─ Retriever Node ────────► (skipped for conversational turns)
   │     1. Embed query (Gemini, with sentence-transformers fallback)
   │     2. Vector search in Qdrant (top 15)
   │     3. Cross-encoder rerank via FlashRank (top 5)
   │
   └─ Responder Node ────────► LLM synthesizes final answer using
                                 retrieved context + conversation history,
                                 routed through the Portkey gateway
   │
   ▼
FastAPI response (answer, reasoning trace, sources, status)
```

The graph is orchestrated with **LangGraph**, using a `MemorySaver` checkpointer keyed by `thread_id` so multi-turn conversations retain context across requests.

## Key Components

| Component | Purpose | Tech |
|---|---|---|
| **Agent Orchestration** | Stateful graph routing between planning, retrieval, and generation | LangGraph |
| **Guardrails** | Blocks off-topic questions and prompt-injection/jailbreak attempts before the agent runs | NeMo Guardrails (Colang rules) |
| **Vector Store** | Stores and searches document embeddings | Qdrant |
| **Embeddings** | Converts text to vectors, with automatic failover | Gemini `gemini-embedding-2-preview` (3072-dim) → `sentence-transformers/all-mpnet-base-v2` (768-dim) fallback |
| **Reranking** | Cross-encoder re-scoring of retrieved chunks for precision | FlashRank (local ONNX, `ms-marco-MiniLM-L-6-v2`) |
| **LLM Gateway** | Unified LLM access with caching, retries, and fallback routing | Portkey (fronting Groq `llama-3.3-70b-versatile`) |
| **Observability** | Distributed tracing across the entire pipeline | Logfire |
| **Ingestion** | Parses, chunks, embeds, and indexes source documents | Custom loaders (PDF, HTML, TXT, DOCX/PPTX) + paragraph-aware chunker |
| **Evaluation** | Automated RAG quality scoring | RAGAS (Faithfulness, Answer Relevancy, Context Precision/Recall, Answer Correctness) + custom Tool Correctness metric |
| **API** | Serves the agent over HTTP | FastAPI |
| **UI** | Interactive chat interface for testing | Streamlit |

## Repository Structure

```
Production_Grade_Agentic_Rag/
├── app/
│   ├── main.py                  # FastAPI app — /query, /graph, / endpoints
│   ├── config.py                # Centralized settings (env-driven)
│   ├── agents/
│   │   ├── graph.py               # LangGraph StateGraph definition & routing
│   │   ├── state.py                # Shared agent state schema
│   │   └── nodes/
│   │       ├── planner.py          # Intent classification / query refinement
│   │       ├── retriever.py        # Vector search + reranking
│   │       └── responder.py        # Final answer synthesis (via Portkey)
│   ├── guardrails/
│   │   ├── rails.py                # NeMo Guardrails initialization & gate
│   │   └── colang_rules.py         # Off-topic / jailbreak / dialog flow definitions
│   ├── gateway/
│   │   ├── client.py               # Portkey-backed LLM client (cache/fallback/retry)
│   │   └── callbacks.py            # LangChain callback for gateway tracing
│   ├── services/retrieval/
│   │   ├── embeddings.py           # Embedding model orchestration + fallback logic
│   │   ├── qdrant_service.py       # Vector search against Qdrant
│   │   └── ranking_service.py      # FlashRank cross-encoder reranking
│   └── ingestion/
│       ├── processor.py            # End-to-end ingestion pipeline (parse→chunk→embed→index)
│       ├── loaders/                # PDF / HTML / text / Office document parsers
│       └── chunking/splitter.py    # Paragraph-aware text chunker
├── evals/
│   ├── pipeline.py                 # Eval orchestration
│   ├── metrics.py                  # RAGAS metric computation (rate-limit aware, batched)
│   ├── guardrails_eval.py          # Guardrail effectiveness testing
│   ├── golden_dataset.json         # Reference Q&A pairs for evaluation
│   └── app.py                      # Eval dashboard
├── ui/
│   └── app.py                      # Streamlit chat interface
├── data/                            # Raw source documents (true/noisy sample sets)
├── processed_data/                  # Parsed + chunked output from the ingestion pipeline
└── requirements.txt
```

## How It Works

1. **Guardrail gate** — Every incoming query first passes through NeMo Guardrails, which uses a fast Groq model (`llama-3.1-8b-instant`) to detect off-topic requests, jailbreak attempts, greetings, and farewells via Colang-defined flows. If a rail fires, the pipeline returns immediately without touching retrieval or the main LLM.
2. **Planning** — The planner node inspects the full conversation history and decides whether the latest message can be answered conversationally (from memory) or needs fresh technical retrieval, producing a refined search query in the latter case.
3. **Retrieval** — For technical queries, the query is embedded and searched against a Qdrant collection (top 15 candidates), then reranked by a local cross-encoder (FlashRank) down to the top 5 most relevant chunks — trading vector search's speed for cross-encoder precision only where it matters.
4. **Generation** — The responder node builds a prompt from retrieved context and conversation history, then calls the LLM through the Portkey gateway (enabling semantic caching, automatic retries on rate limits/errors, and fallback to a secondary model).
5. **Memory** — LangGraph's `MemorySaver` checkpointer persists state per `thread_id`, so follow-up questions in the same conversation retain context without re-sending full history from the client.
6. **Ingestion (offline)** — Documents are parsed by format-specific loaders, split into paragraph-bounded chunks (~1500 chars), embedded, and upserted into Qdrant with source metadata — run independently via `python -m app.ingestion.processor`.
7. **Evaluation (offline)** — The eval harness scores the pipeline's real outputs against a golden dataset using RAGAS metrics (Faithfulness, Answer Relevancy, Context Precision, Context Recall, Answer Correctness) plus a custom Tool Correctness (Jaccard) metric, with rate-limit-aware batching for Groq's free tier.

## Installation

```bash
git clone https://github.com/vigmallya/Production_Grade_Agentic_Rag.git
cd Production_Grade_Agentic_Rag
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root with:

```bash
# Vector DB (Qdrant)
QDRANT_API_KEY=
QDRANT_CLUSTER_ENDPOINT=

# Embeddings (Gemini)
GEMINI_API_KEY=

# LLM (Groq)
GROQ_API_KEY=
GROQ_FALLLBACK_API_KEY=

# LLM Gateway (Portkey)
PORTKEY_API_KEY=
PORTKEY_CONFIG_ID=

# Observability (Logfire)
LOGFIRE_TOKEN=

# Environment
ENVIRONMENT=dev
```

> Note: Portkey slugs (`GROQ_SLUG`, `GEMINI_SLUG`) map to provider integrations configured on your Portkey dashboard — set these up under your Portkey account and match the slugs in `app/config.py`.

## Usage

### 1. Ingest documents

```bash
python -m app.ingestion.processor data --wipe
```
Parses everything under `data/` (routing subfolders like `true_data/` and `noisy_sample_10/` to labeled sources), chunks, embeds, and indexes into Qdrant. Pass `--wipe` to drop and recreate the collection first.

### 2. Run the API

```bash
uvicorn app.main:app --reload
```
- `GET /` — health check
- `GET /graph` — renders the LangGraph agent workflow as a PNG
- `POST /query` — main endpoint

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"q": "How do I configure SR-IOV on an Intel NIC?", "thread_id": "user-123"}'
```

### 3. Run the UI

```bash
streamlit run ui/app.py
```
A chat interface for interactively testing the agent, showing live reasoning trace, sources, and cache-hit status.

### 4. Run evaluations

```bash
python evals/pipeline.py
```
Scores pipeline outputs against `evals/golden_dataset.json` using RAGAS metrics. Uses a separate judge API key (`JUDGE_GROQ`) so evaluation runs don't compete with production traffic for rate limits.

## Design Notes

- **Why a gateway (Portkey) instead of calling Groq directly?** It adds semantic caching, automatic retries on rate limits, and fallback to a secondary model/provider — without changing the LangChain-facing interface (`ChatOpenAI` is used as a drop-in, since Portkey exposes an OpenAI-compatible proxy endpoint).
- **Why rerank after vector search?** Cosine similarity retrieval is fast but approximate; a cross-encoder reranker is more precise but too slow to run over an entire corpus. Retrieving broadly (top 15) then reranking narrowly (top 5) with a lightweight local ONNX model balances both.
- **Why an embedding fallback?** The primary embedding call (Gemini) is probed once at startup; if it's unreachable, the system transparently switches to a local `sentence-transformers` model rather than failing ingestion or queries outright.
- **Why guardrails before the agent graph, not inside it?** Keeping the gate outside LangGraph means off-topic/jailbreak queries never consume retrieval or generation resources — a cheap, fast model filters traffic before the expensive path runs.

## Known Limitations

- The chunker (`chunk_text`) is a simple paragraph-based splitter, not a semantic or token-aware chunker — very large paragraphs are not split further.
- The eval pipeline is tuned around Groq's free-tier rate limits (batching + cooldowns) and will run slowly by design; a paid tier would allow much faster evaluation.
- Guardrail topic/jailbreak detection is example-based (few-shot Colang definitions), not a trained classifier — coverage is only as good as the listed examples.
