"""
Configuration — environment loading and LLM initialization.
"""
# (Module docstring: says this file loads environment and sets up the LLM.)

import os
# import the operating system library so we can read environment variables

from dotenv import load_dotenv
# import a helper to load variables from a .env file into the environment

from langchain_openai import ChatOpenAI
# import the ChatOpenAI client used to talk to the language model

# Load .env file (if present) into environment variables
load_dotenv()
# read a .env file and add its values to the process environment, if the file exists

# Validate that the API key is set
if not os.environ.get("OPENAI_API_KEY"):
    # check if OPENAI_API_KEY is present in environment variables
    raise EnvironmentError(
        "OPENAI_API_KEY is not set. "
        "Copy .env.example to .env and add your key, or export it directly."
    )
    # if not set, stop and tell the user how to set it

# Shared LLM instance
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
# create a ChatOpenAI client with a chosen model and no randomness (temperature=0)
