import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("SERPAPI_KEY")

if api_key is None:
    print("No key found. Is SERPAPI_KEY in your .env file?")
else:
    print("Key loaded! It starts with:", api_key[:4])