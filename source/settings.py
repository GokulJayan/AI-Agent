import os

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("NVIDIA_API_KEY")
MODEL = os.getenv("NVIDIA_LLM_MODEL")
BASE_URL = "https://integrate.api.nvidia.com/v1"

if not API_KEY:
    raise ValueError("NVIDIA_API_KEY is not set in .env")

if not MODEL:
    raise ValueError("NVIDIA_LLM_MODEL is not set in .env")
