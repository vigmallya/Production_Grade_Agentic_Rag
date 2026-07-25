import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY")
    QDRANT_CLUSTER_ENDPOINT: str = os.getenv("QDRANT_CLUSTER_ENDPOINT")
    QDRANT_COLLECTION: str = "enterprise_rag"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")

    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    GROQ_FALLLBACK_API_KEY: str = os.getenv("GROQ_FALLLBACK_API_KEY")
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

settings = Settings()