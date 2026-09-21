import os

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("NVIDIA_API_KEY")
MODEL = os.getenv("NVIDIA_LLM_MODEL")
BASE_URL = "https://integrate.api.nvidia.com/v1"

# Removed the immediate ValueError raises to prevent CI from crashing during imports.
# Validation should now happen at the time of API call if needed.
# if not API_KEY:
#     raise ValueError("NVIDIA_API_KEY is not set in .env")

# if not MODEL:
#     raise ValueError("NVIDIA_LLM_MODEL is not set in .env")

