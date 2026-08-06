import os
from dotenv import load_dotenv

load_dotenv()

class Settings:

     # --- VECTOR DB (QDRANT) ---
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY")
    QDRANT_CLUSTER_ENDPOINT: str = os.getenv("QDRANT_CLUSTER_ENDPOINT")
    QDRANT_COLLECTION: str = "enterprise_rag"

    # --- EMBEDDING MODEL (GEMINI) ---
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")

    # --- REASONING ENGINE (GROQ) ---
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    GROQ_FALLLBACK_API_KEY: str = os.getenv("GROQ_FALLLBACK_API_KEY")
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # --- LLM GATEWAY (PORTKEY) ---
    PORTKEY_API_KEY = os.getenv("PORTKEY_API_KEY")
    GROQ_SLUG =  "prodagenticrag"     # primary: @prodagenticrag/llama-3.3-70b-versatile
    GEMINI_SLUG = "prodagenticrag2"  # fallback: @prodagenticrag2/gemini-3-flash-preview
    PORTKEY_CONFIG_ID = os.getenv("PORTKEY_CONFIG_ID")  # Portkey config ID for the gateway

    # --- ENVIRONMENT ---
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev")  # dev, staging, prod

settings = Settings()