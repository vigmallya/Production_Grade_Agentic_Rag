import logfire
from langchain_core.callbacks import BaseCallbackHandler


class PortkeyCallback(BaseCallbackHandler):
    """
    LangChain callback for Portkey/LangChain observability.
    Captures token usage and LLM metadata.
    """

    def on_llm_end(self, response, **kwargs):
        try:
            llm_output = response.llm_output or {}

            logfire.info(
                "LLM call completed",
                token_usage=llm_output.get("token_usage"),
                model=response.generations[0][0].message.response_metadata.get(
                    "model_name",
                    "unknown"
                )
                if response.generations
                else "unknown",
            )

        except Exception as e:
            logfire.warning(
                "Failed to extract LLM metadata",
                error=str(e)
            )