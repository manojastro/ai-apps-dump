"""Chat model adapters and the factory that picks one from configuration."""

from invoiceflow.config import ConfigError, Settings
from invoiceflow.ports.llm import ChatModel


def build_chat_model(settings: Settings) -> ChatModel:
    if settings.llm_provider == "stub":
        from invoiceflow.adapters.llm.stub import StubChatModel

        return StubChatModel()
    from invoiceflow.adapters.llm.openai_compat import OpenAICompatibleChatModel

    model = settings.require("llm_endpoint")
    if settings.llm_provider == "databricks":
        from databricks.sdk import WorkspaceClient

        client = WorkspaceClient(
            profile=settings.databricks_config_profile
        ).serving_endpoints.get_open_ai_client()  # type: ignore[no-untyped-call]
        return OpenAICompatibleChatModel(client, model, provider="databricks")
    if settings.llm_provider == "azure_openai":
        import os

        from openai import AzureOpenAI

        api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        if not api_key:
            raise ConfigError("AZURE_OPENAI_API_KEY must come from the environment or Key Vault")
        client = AzureOpenAI(
            azure_endpoint=settings.require("azure_openai_endpoint"),
            api_version=settings.require("azure_openai_api_version"),
            api_key=api_key,
        )
        return OpenAICompatibleChatModel(
            client, settings.azure_openai_deployment or model, provider="azure_openai"
        )
    raise ConfigError(f"unknown LLM provider {settings.llm_provider}")
