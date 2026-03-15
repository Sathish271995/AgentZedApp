"""
azure_client.py
===============
Single shared helper that builds an AzureOpenAI client from environment variables.
All agents import get_azure_client() and get_deployment() from here — so there is
only ONE place to change if credentials or deployment names ever change.

Required .env keys:
    AZURE_OPENAI_ENDPOINT       e.g. https://testchatgpt1.openai.azure.com/
    AZURE_OPENAI_KEY            your Azure OpenAI resource key
    AZURE_OPENAI_API_VERSION    e.g. 2024-12-01-preview
    AZURE_OPENAI_CHAT_DEPLOYMENT  e.g. gpt4v
"""

import logging
import os

from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()
logger = logging.getLogger("azure_client")


def get_azure_client() -> AzureOpenAI | None:
    """
    Build and return an AzureOpenAI client using environment variables.
    Returns None if any required variable is missing, so callers can
    fall back gracefully without crashing.
    """
    endpoint   = os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
    api_key    = os.getenv("AZURE_OPENAI_KEY", "")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

    if not endpoint or not api_key:
        logger.warning(
            "Azure OpenAI credentials not set. "
            "Add AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY to .env"
        )
        return None

    return AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
    )


def get_deployment() -> str:
    """
    Return the chat deployment name from env.
    Falls back to 'gpt4v' if not set.
    """
    return os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt4v")
