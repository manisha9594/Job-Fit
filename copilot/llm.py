"""LLM factory: Gemini (free tier) → Groq (free tier) → OpenAI → demo stub.

Gemini and Groq both expose OpenAI-compatible chat endpoints, so one
langchain-openai ChatOpenAI client covers all three providers. With no key
set, DemoChatModel answers deterministically — the analysis modules fall back
to rule-based heuristics in demo mode, so the whole pipeline runs offline.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class DemoChatModel(BaseChatModel):
    """Deterministic stand-in used when no API key is configured."""

    @property
    def _llm_type(self) -> str:
        return "demo-chat"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        human_text = next(
            (m.content for m in reversed(messages) if m.type == "human"), ""
        )
        return ChatResult(generations=[ChatGeneration(message=AIMessage(
            content="[demo mode — set GEMINI_API_KEY, GROQ_API_KEY or "
                    "OPENAI_API_KEY for live LLM answers]\n"
            f"Received {len(human_text)} chars of input. "
            "Live mode would return structured JSON here."
        ))])

    def bind_tools(self, tools, **kwargs):
        return self


_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def llm_provider() -> str:
    """Name of the configured provider, or 'demo'."""
    # Re-read .env each time so adding/changing a key needs no server restart.
    if _ENV_FILE.is_file() and "PYTEST_CURRENT_TEST" not in os.environ:
        load_dotenv(_ENV_FILE, override=True)
    if os.getenv("GEMINI_API_KEY"):
        return "gemini"
    if os.getenv("GROQ_API_KEY"):
        return "groq"
    if os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY"):
        return "openai"
    return "demo"


def is_demo_mode() -> bool:
    return llm_provider() == "demo"


def get_chat_model():
    """Return a chat model for the first configured provider, else the demo stub."""
    provider = llm_provider()
    if provider == "demo":
        return DemoChatModel()

    from langchain_openai import ChatOpenAI

    if provider == "gemini":
        return ChatOpenAI(
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            api_key=os.environ["GEMINI_API_KEY"],
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            temperature=0.2,
        )
    if provider == "groq":
        return ChatOpenAI(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            api_key=os.environ["GROQ_API_KEY"],
            base_url="https://api.groq.com/openai/v1",
            temperature=0.2,
        )
    return ChatOpenAI(
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL") or None,
        temperature=0.2,
    )
