# 🚀 Project State & Post-Reset Quick-Start Guide

> **Project:** Autonomous Business Intelligence Multi-Agent System (Olist BI)  
> **Last Updated:** 2026-09-30  
> **Current Progress:** Phase 1 Complete (Database & ETL) | Phase 2 Ready to Begin  

---

## 📌 Executive Summary of What Was Built So Far

### 1. Architectural Decisions (Locked-in & Verified)
* **Dataset Domain**: Brazilian E-Commerce (Olist) — 100,000 real orders, ~550,000 records across 7 relational tables, translated to English, with full referential integrity.
* **Database Architecture**: 
  * **PostgreSQL 16 (Docker Compose)**: Source-of-truth transactional database with dedicated `olist_admin` and strict least-privilege `olist_readonly` users.
  * **DuckDB (Embedded In-Memory OLAP)**: Attaches directly to PostgreSQL via `postgres_scanner` with `READ_ONLY` mode, executing columnar vectorized aggregations in milliseconds with zero data duplication.
* **AI Architecture**: 4-Agent Collaborative Pod in `LangGraph`:
  1. *Chief Orchestrator Agent* (Supervisor)
  2. *SQL Engineer Agent* (DuckDB query crafter)
  3. *Data QA & Critic Agent* (Adversarial auditor checking logic, safety, and metric formulas)
  4. *BI Storyteller Agent* (Business narrative + dynamic Recharts JSON configuration)
* **LLM Strategy**: Dual-engine `LLMFactory`:
  * Local GPU: `Ollama` running `qwen2.5-coder:7b` (NVIDIA RTX 3050 + 24GB RAM, 0 rate limits, 100% offline).
  * Cloud: Google AI Studio API (`gemini-2.5-flash` / `gemini-1.5-flash` free tier).
* **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, `shadcn/ui`, Recharts, consuming Server-Sent Events (SSE) via custom HTTP POST streaming.
* **Package Management**: Switching to **`uv`** (by Astral) for instant virtual environments and dependency resolution.

### 2. Physical Codebase Assets Created
* `docker-compose.yml`: PostgreSQL 16 Alpine container with persistent volume and healthcheck.
* `docker/init.sql`: Creates `olist_readonly` role with `GRANT SELECT` and `ALTER DEFAULT PRIVILEGES`.
* `.env.example`: Template for environment secrets (database ports, credentials).
* `backend/app/db/schema.sql`: Complete DDL for all 7 tables (`customers`, `sellers`, `products`, `orders`, `order_items`, `order_payments`, `order_reviews`) with primary keys, foreign keys, and indexes.
* `backend/scripts/seed_olist.py`: Automated ETL pipeline that streams the Olist zip, cleans missing values, merges Portuguese-to-English translations, and loads ~550,000 records in batches of 5,000 using `psycopg` (v3).
* `docs/ARCHITECTURE.md`: Master architectural specification with Mermaid sequence and component diagrams.

---

## 💻 Post-Reset Re-Installation Checklist

When you finish resetting your laptop, follow these steps to resume work in under 5 minutes:

### Step 1: Install Core Software Tools
1. **Git**:
   ```powershell
   winget install Git.Git
   ```
2. **Python** (Python 3.11 or 3.12):
   ```powershell
   winget install Python.Python.3.12
   ```
3. **uv** (Modern Python package manager):
   ```powershell
   winget install astral-sh.uv
   ```
4. **Docker Desktop** (for containerized PostgreSQL):
   ```powershell
   winget install Docker.DockerDesktop
   ```
   *Open Docker Desktop once after install and ensure the whale icon is green ("Engine running").*
5. **Node.js** (for Phase 4 Next.js frontend):
   ```powershell
   winget install OpenJS.NodeJS.LTS
   ```

---

### Step 2: Clone & Restore Project
1. Clone your repository:
   ```powershell
   git clone <YOUR_GITHUB_REPO_URL>
   cd "business agent"
   ```
2. Switch to your feature branch:
   ```powershell
   git checkout feat/fastapi-backend-foundation
   ```
3. Re-create your local `.env` file (copied from `.env.example`):
   ```powershell
   copy .env.example .env
   ```

---

### Step 3: Spin Up PostgreSQL Database
1. Launch the PostgreSQL Docker container:
   ```powershell
   docker compose up -d
   ```
2. Apply the schema DDL:
   ```powershell
   docker exec -i olist_postgres psql -U olist_admin -d olist_db < backend/app/db/schema.sql
   ```

---

### Step 4: Setup Python Environment with `uv`
1. Create a virtual environment using `uv`:
   ```powershell
   uv venv
   ```
2. Activate it:
   * **PowerShell**:
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
   * **Git Bash**:
     ```bash
     source .venv/Scripts/activate
     ```
3. Install all dependencies with `uv`:
   ```powershell
   uv pip install -r backend/requirements.txt
   ```
4. Seed the database with the ~550k records:
   ```powershell
   python backend/scripts/seed_olist.py
   ```
5. Verify the data is loaded:
   ```powershell
   docker exec -i olist_postgres psql -U olist_admin -d olist_db -c "SELECT count(*) FROM orders;"
   ```
   *(Should return 99,441 rows)*.

---

## 🎯 Progress Milestones

### Phase 1: Database & Data Ingestion (✅ Complete)
* PostgreSQL 16 running via Docker Compose (`olist_postgres`).
* All 7 tables created with foreign keys and indexes.
* ~550,000 records seeded from Olist dataset (99,441 orders).
* Dedicated `olist_readonly` user configured with least-privilege `SELECT`.

### Phase 2: FastAPI Backend Foundation & Analytical Semantic Layer (✅ Complete)
* **`backend/app/core/config.py`**: Pydantic `BaseSettings` loading `.env` variables with strict type validation.
* **`backend/app/core/semantic_layer.yaml`**: Standard business metric definitions (GMV, AOV, CSAT, On-Time Delivery Rate) and canonical join graphs.
* **`backend/app/core/validator.py`**: SQL AST validation using `sqlglot` enforcing strictly read-only `SELECT` statements and schema table guardrails.
* **`backend/app/db/duckdb_client.py`**: In-memory DuckDB OLAP manager attached to PostgreSQL via `postgres_scanner` with `memory.main` logical views.
* **`backend/app/main.py`**: FastAPI application exposing `/health`, `/api/v1/query`, `/api/v1/validate`, `/api/v1/semantic-layer`, `/api/v1/metrics`, and `/api/v1/schema`.
* **Testing Suite**: 23 automated unit and integration tests passing (`pytest`) verifying AST validation, database latency, and API endpoints.

---

## 🚀 Next Milestone: Phase 3 (LangGraph Multi-Agent Pod)

With the backend foundation and DuckDB OLAP engine in place, we proceed to **Phase 3**:

1. **`backend/app/agent/llm_factory.py`**: Dual-provider LLM abstraction supporting Google AI Studio (Gemini 2.5 Flash free tier) and local Ollama (`qwen2.5-coder:7b`).
2. **`backend/app/agent/state.py`**: Pydantic `AgentState` schema tracking user query, pruned schema, candidate SQL, AST validation status, execution outputs, reflection trace, and narrative visualization spec.
3. **`backend/app/agent/nodes/`**:
   * `schema_pruner.py`: Filters the schema down to only relevant tables and metrics.
   * `sql_generator.py`: Generates few-shot DuckDB SQL grounded in `semantic_layer.yaml`.
   * `sql_critic.py`: Adversarial QA evaluating logic, edge cases, and query plan efficiency.
   * `query_executor.py`: Runs SQL against `DuckDBManager` with 3-attempt reflection loop.
   * `storyteller.py`: Synthesizes executive bullet points and typed Recharts JSON specs.
4. **`backend/app/api/v1/chat.py`**: Server-Sent Events (SSE) streaming endpoint for live real-time token/status streaming.

