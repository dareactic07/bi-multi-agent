"""Dual-provider LLM Factory supporting Google Gemini and local Ollama with fallback."""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from backend.app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class RuleBasedFallbackChatModel(BaseChatModel):
    """Deterministic, zero-cloud fallback model for testing and offline execution.

    Synthesizes valid DuckDB SQL and Recharts specs directly using pattern matching
    and semantic rules when external LLM credentials are not configured.
    """

    model_name: str = "bi-rule-fallback"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        full_prompt = " ".join([m.content for m in messages if isinstance(m.content, str)])
        prompt_lower = full_prompt.lower()

        # 1. Orchestrator classification step
        if "chief orchestrator" in prompt_lower or "classify their analytical intent" in prompt_lower:
            tables = ["orders"]
            metrics = ["order_volume"]

            if any(w in prompt_lower for w in ["revenue", "sales", "gmv", "amount", "price", "category", "product"]):
                tables.extend(["order_items", "products"])
                metrics.append("gmv")
            if any(w in prompt_lower for w in ["customer", "state", "city", "location"]):
                tables.append("customers")
            if any(w in prompt_lower for w in ["review", "rating", "csat", "score"]):
                tables.append("order_reviews")
                metrics.append("csat")
            if any(w in prompt_lower for w in ["payment", "installments"]):
                tables.append("order_payments")

            unique_tables = sorted(list(set(tables)))
            response_json = {
                "intent": "E-Commerce analytical business query",
                "relevant_tables": unique_tables,
                "relevant_metrics": metrics,
                "pruned_context": f"Relevant tables: {', '.join(unique_tables)} with metrics {', '.join(metrics)}",
            }
            content = json.dumps(response_json)

        # 2. SQL Engineer step
        elif "expert sql engineer" in prompt_lower or "write a single, optimized" in prompt_lower:
            if "status" in prompt_lower or "by status" in prompt_lower:
                sql = (
                    "SELECT order_status, COUNT(*) AS total_orders "
                    "FROM orders "
                    "GROUP BY order_status "
                    "ORDER BY total_orders DESC;"
                )
            elif "category" in prompt_lower or "product" in prompt_lower or "revenue" in prompt_lower or "top 5" in prompt_lower:
                sql = (
                    "SELECT p.category_name, ROUND(SUM(oi.price), 2) AS total_revenue "
                    "FROM orders o "
                    "JOIN order_items oi ON o.order_id = oi.order_id "
                    "JOIN products p ON oi.product_id = p.product_id "
                    "WHERE o.order_status = 'delivered' "
                    "GROUP BY p.category_name "
                    "ORDER BY total_revenue DESC "
                    "LIMIT 5;"
                )
            elif "state" in prompt_lower or "customer" in prompt_lower:
                sql = (
                    "SELECT c.state, COUNT(DISTINCT o.order_id) AS total_orders "
                    "FROM orders o "
                    "JOIN customers c ON o.customer_id = c.customer_id "
                    "GROUP BY c.state "
                    "ORDER BY total_orders DESC "
                    "LIMIT 10;"
                )
            elif "monthly" in prompt_lower or "trend" in prompt_lower or "time" in prompt_lower:
                sql = (
                    "SELECT DATE_TRUNC('month', purchase_timestamp) AS order_month, COUNT(*) AS total_orders "
                    "FROM orders "
                    "GROUP BY 1 "
                    "ORDER BY 1 ASC "
                    "LIMIT 12;"
                )
            else:
                sql = (
                    "SELECT order_status, COUNT(*) AS count "
                    "FROM orders "
                    "GROUP BY order_status "
                    "ORDER BY count DESC "
                    "LIMIT 5;"
                )
            content = f"```sql\n{sql}\n```"

        # 3. SQL Critic step
        elif "data qa & sql critic" in prompt_lower or "audit the generated sql" in prompt_lower:
            response_json = {
                "approved": True,
                "issues": [],
                "corrected_sql": None,
            }
            content = json.dumps(response_json)

        # 4. Storyteller / Visualization step
        elif "executive bi storyteller" in prompt_lower or "produce:" in prompt_lower:
            response_json = {
                "insights": (
                    "### Key Business Insights\n"
                    "- The analytical query executed successfully across the Olist dataset.\n"
                    "- High concentration observed among the top segments.\n"
                    "- Recommend focusing supply chain optimization on peak volume channels."
                ),
                "chart_spec": {
                    "chart_type": "bar",
                    "title": "Business Intelligence Breakdown",
                    "x_axis_key": "category_name",
                    "y_axis_keys": ["total_revenue"],
                    "summary": "Key performance metrics distributed by primary category dimension.",
                },
            }
            content = json.dumps(response_json)

        else:
            content = "OK"

        generation = ChatGeneration(message=AIMessage(content=content))
        return ChatResult(generations=[generation])

    @property
    def _llm_type(self) -> str:
        return "bi-rule-fallback"


class LLMFactory:
    """Factory to construct ChatModel instances based on environment configuration."""

    @staticmethod
    def get_chat_model(
        provider: Optional[str] = None,
        settings: Optional[Settings] = None,
    ) -> BaseChatModel:
        """Instantiate the configured LLM provider.

        Args:
            provider: 'gemini', 'ollama', or 'mock'. If None, reads settings.DEFAULT_LLM_PROVIDER.
            settings: Optional app settings instance.

        Returns:
            A LangChain BaseChatModel instance.
        """
        cfg = settings or get_settings()
        chosen_provider = (provider or cfg.DEFAULT_LLM_PROVIDER).lower()

        # 1. Google Gemini Cloud Provider
        if chosen_provider == "gemini":
            api_key = cfg.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
            if api_key and api_key != "your_gemini_api_key_here":
                try:
                    from langchain_google_genai import ChatGoogleGenerativeAI

                    logger.info(f"Initializing Google Gemini Chat Model ({cfg.GEMINI_MODEL})...")
                    return ChatGoogleGenerativeAI(
                        model=cfg.GEMINI_MODEL,
                        google_api_key=api_key,
                        temperature=0.1,
                    )
                except Exception as exc:
                    logger.warning(
                        f"Failed to initialize ChatGoogleGenerativeAI: {exc}. Falling back to RuleBasedFallbackChatModel."
                    )
            else:
                logger.info(
                    "GEMINI_API_KEY is not set or placeholder. Utilizing RuleBasedFallbackChatModel for offline operation."
                )
                return RuleBasedFallbackChatModel()

        # 2. Local Ollama Provider
        if chosen_provider == "ollama":
            try:
                # Use standard LangChain ChatOpenAI interface pointed to Ollama's OpenAI-compatible /v1 endpoint
                from langchain_community.chat_models import ChatOllama

                logger.info(f"Initializing Ollama Chat Model ({cfg.OLLAMA_MODEL}) at {cfg.OLLAMA_BASE_URL}...")
                return ChatOllama(
                    model=cfg.OLLAMA_MODEL,
                    base_url=cfg.OLLAMA_BASE_URL,
                    temperature=0.1,
                )
            except Exception as exc:
                logger.warning(f"Ollama initialization failed: {exc}. Using fallback model.")
                return RuleBasedFallbackChatModel()

        # 3. Default to Fallback Model
        return RuleBasedFallbackChatModel()
