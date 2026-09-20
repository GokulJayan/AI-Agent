from openai import OpenAI

from .settings import API_KEY, BASE_URL

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
    timeout=120.0,
)
