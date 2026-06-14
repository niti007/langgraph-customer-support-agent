"""
Configuration — environment loading and LLM initialization.
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load .env file (if present) into environment variables
load_dotenv()

# Validate that the API key is set
if not os.environ.get("OPENAI_API_KEY"):
    raise EnvironmentError(
        "OPENAI_API_KEY is not set. "
        "Copy .env.example to .env and add your key, or export it directly."
    )

# Shared LLM instance
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
