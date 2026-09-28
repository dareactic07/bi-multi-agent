# 📊 Autonomous Business Intelligence Agent (Olist BI)

A production-grade, collaborative multi-agent business intelligence system that converts natural language business queries into verified DuckDB/PostgreSQL analytical queries, self-heals execution errors, and streams real-time insights with dynamic Recharts visualizations.

## 🛠️ Tech Stack
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, shadcn/ui, Recharts
- **Backend**: FastAPI, Async Python, Pydantic v2
- **Data Engine**: PostgreSQL (Docker) + Embedded DuckDB (Columnar OLAP)
- **AI Core**: LangGraph Multi-Agent Pod (Orchestrator, SQL Engineer, Critic, Storyteller)
- **LLM**: Local Ollama (Qwen 2.5 Coder 7B on RTX 3050 GPU) + Gemini 2.5 Flash Cloud Fallback

## 📖 Architecture & Design
See detailed documentation in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).