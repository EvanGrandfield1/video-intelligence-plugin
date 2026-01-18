#!/usr/bin/env python3
"""
Live Context Box: Extract keywords from transcript segments,
perform semantic search against document chunks, and surface relevant content.
"""
import argparse
import json
import os
import sys
from typing import List, Dict

from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


def load_transcript(transcript_path: str) -> List[Dict]:
    """Load transcript JSON."""
    with open(transcript_path, "r") as f:
        data = json.load(f)
    return data.get("segments", [])


def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
    """Extract keywords using simple TF-based approach or OpenAI."""
    # Simple approach: use most significant words
    import re
    
    # Common stopwords
    stopwords = set([
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "can", "must", "shall", "to", "of", "in",
        "for", "on", "with", "at", "by", "from", "as", "into", "through",
        "during", "before", "after", "above", "below", "between", "under",
        "again", "further", "then", "once", "here", "there", "when", "where",
        "why", "how", "all", "each", "few", "more", "most", "other", "some",
        "such", "no", "nor", "not", "only", "own", "same", "so", "than",
        "too", "very", "just", "and", "but", "if", "or", "because", "until",
        "while", "this", "that", "these", "those", "i", "you", "he", "she",
        "it", "we", "they", "what", "which", "who", "whom", "its", "his",
        "her", "their", "our", "my", "your", "up", "out", "about", "over"
    ])
    
    # Tokenize and filter
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    filtered = [w for w in words if w not in stopwords]
    
    # Count frequencies
    freq = {}
    for w in filtered:
        freq[w] = freq.get(w, 0) + 1
    
    # Sort by frequency and return top keywords
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w[0] for w in sorted_words[:max_keywords]]


def get_embedding(text: str) -> List[float]:
    """Get embedding for text using OpenAI API."""
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not set", file=sys.stderr)
        return []

    import requests

    response = requests.post(
        "https://api.openai.com/v1/embeddings",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "input": text,
            "model": "text-embedding-3-small"
        }
    )
    response.raise_for_status()
    return response.json()["data"][0]["embedding"]


def semantic_search(query_embedding: List[float], doc_id: str, top_n: int = 3) -> List[Dict]:
    """Search for similar chunks in Supabase using pgvector."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Supabase credentials not set", file=sys.stderr)
        return []

    import requests

    # Call Supabase RPC function for vector similarity search
    # This assumes you have a function called 'match_doc_chunks' in Supabase
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/rpc/match_doc_chunks",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "query_embedding": query_embedding,
            "match_count": top_n,
            "filter_doc_id": doc_id
        }
    )

    if response.status_code == 200:
        return response.json()
    else:
        # Fallback: try direct table query (less efficient)
        print(f"⚠️ RPC not available, using fallback search", file=sys.stderr)
        return fallback_search(doc_id, top_n)


def fallback_search(doc_id: str, top_n: int) -> List[Dict]:
    """Fallback search without vector similarity (returns first N chunks)."""
    import requests

    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/document_chunks",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
        },
        params={
            "doc_id": f"eq.{doc_id}",
            "select": "content,chunk_index",
            "limit": top_n
        }
    )

    if response.status_code == 200:
        return response.json()
    return []


def process_live_context(transcript_path: str, doc_id: str, top_n: int = 3):
    """Process transcript and output live context for each segment."""
    segments = load_transcript(transcript_path)

    for seg in segments:
        text = seg.get("text", "")
        if not text.strip():
            continue

        # Extract keywords
        keywords = extract_keywords(text)

        # Get embedding for the segment text
        try:
            embedding = get_embedding(text)
            matches = semantic_search(embedding, doc_id, top_n) if embedding else []
        except Exception as e:
            print(f"⚠️ Search error: {e}", file=sys.stderr)
            matches = []

        # Output result
        result = {
            "segment": {
                "start": seg.get("start"),
                "end": seg.get("end"),
                "speaker": seg.get("speaker"),
                "text": text
            },
            "keywords": keywords,
            "context_matches": matches
        }

        print(json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Live Context Box")
    parser.add_argument("transcript_path", help="Path to transcript JSON")
    parser.add_argument("--doc_id", required=True, help="Document ID to search against")
    parser.add_argument("--top_n", type=int, default=3, help="Number of top matches to return")

    args = parser.parse_args()

    if not os.path.exists(args.transcript_path):
        print(f"❌ Transcript not found: {args.transcript_path}")
        sys.exit(1)

    process_live_context(args.transcript_path, args.doc_id, args.top_n)
