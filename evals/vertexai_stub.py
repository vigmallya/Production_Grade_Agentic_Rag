"""
Stub for ragas's broken internal import.

ragas/llms/base.py (both 0.3.9 and 0.4.3) does:
    from langchain_community.chat_models.vertexai import ChatVertexAI

That class was removed from langchain-community once it crossed the version
where the long-deprecated VertexAI integration was finally deleted (it moved
to the separate langchain-google-vertexai package years ago). Since this repo
never uses VertexAI at all (LLM calls go through Groq via Portkey), we don't
need a working ChatVertexAI — we just need ragas's import line to succeed.

Import this BEFORE anything imports ragas (i.e. at the very top of
evals/__init__.py or evals/app.py, above `from evals.metrics import ...`).
"""

import sys
import types


def install_vertexai_stub() -> None:
    module_name = "langchain_community.chat_models.vertexai"
    if module_name in sys.modules:
        return  # already stubbed (or genuinely available) — don't clobber it

    stub = types.ModuleType(module_name)

    class ChatVertexAI:  # placeholder — never instantiated in this codebase
        def __init__(self, *args, **kwargs):
            raise RuntimeError(
                "ChatVertexAI is a stub — this codebase does not use VertexAI. "
                "If you actually need it, install langchain-google-vertexai and "
                "import from there instead."
            )

    stub.ChatVertexAI = ChatVertexAI
    sys.modules[module_name] = stub


install_vertexai_stub()
