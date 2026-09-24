"""
Configuration loader.

Reads from environment variables + .env file.
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


# Default config
DEFAULT_CONFIG = {
    # Cohere (for rerank + LLM)
    "COHERE_API_KEY": "",
    "COHERE_CHAT_MODEL": "command-r-plus",
    "COHERE_RERANK_MODEL": "rerank-english-v3.0",

    # Embeddings (FIXED — see PLAN.md §3.1)
    "EMBEDDING_MODEL": "BAAI/bge-m3",
    "EMBEDDING_DIM": 1024,

    # Vector store
    "VECTOR_STORE_PATH": "./data/chroma_db",
    "VECTOR_STORE_COLLECTIONS": ["sfda_regulations", "user_documents", "templates", "faq"],

    # Excel
    "EXCEL_LOG_PATH": "./data/audit_log.xlsx",

    # LLM client (PLAN.md §7.2 — UnifiedLLMClient)
    "LLM_PROVIDER": "cohere",  # or "openai", "anthropic", "gemini", "local"
}


def load_config(env_path: str | Path = ".env") -> dict:
    """Load configuration from environment + defaults."""
    load_dotenv(env_path)
    config = DEFAULT_CONFIG.copy()
    for key in config:
        if os.getenv(key):
            config[key] = os.getenv(key)
    return config


# SFDA regulatory documents to watch (PLAN.md §8.1)
SFDA_DOCUMENTS = {
    "MDS-G5": {"version": "5.0", "date": "22/06/2020", "name": "Medical Device Listing and Marketing Authorization"},
    "MDS-G008": {"version": "current", "date": "—", "name": "Classification Guidance"},
    "MDS-G010": {"version": "1.0", "date": "03/01/2023", "name": "AI/ML-Enabled Medical Devices"},
    "MDS-G27": {"version": "1.0", "date": "August 2025", "name": "Digital Health Products Guidance"},
    "MDS-REQ9": {"version": "2.0", "date": "11/06/2024", "name": "Licensing of Medical Devices Establishments"},
    "MDS-REQ5": {"version": "6.0", "date": "19/07/2023", "name": "Importation and Shipments Clearance"},
}
