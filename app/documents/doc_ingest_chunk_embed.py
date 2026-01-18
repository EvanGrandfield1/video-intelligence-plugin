#!/usr/bin/env python3
"""
Document ingestion: chunk, embed, and store in Supabase/pgvector.
Supports PDF and TXT files.
"""
import argparse
import json
import os
import sys
from typing import List

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


def extract_text(file_path: str) -> str:
    """Extract text from PDF or TXT file."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    elif ext == ".pdf":
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except ImportError:
            print("❌ pdfplumber not installed. Install with: pip install pdfplumber")
            sys.exit(1)

    else:
        print(f"❌ Unsupported file type: {ext}")
        sys.exit(1)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap

    return chunks


def get_embeddings(texts: List[str]) -> List[List[float]]:
    """Get embeddings from OpenAI API."""
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not set in environment")
        sys.exit(1)

    try:
        import requests

        response = requests.post(
            "https://api.openai.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "input": texts,
                "model": "text-embedding-3-small"
            }
        )
        response.raise_for_status()
        data = response.json()
        return [item["embedding"] for item in data["data"]]

    except Exception as e:
        print(f"❌ Embedding API error: {e}")
        sys.exit(1)


def store_chunks_in_supabase(doc_id: str, chunks: List[str], embeddings: List[List[float]]):
    """Store chunks and embeddings in Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ SUPABASE_URL or SUPABASE_KEY not set in environment")
        sys.exit(1)

    try:
        import requests

        # Insert each chunk
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            row = {
                "doc_id": doc_id,
                "chunk_index": i,
                "content": chunk,
                "embedding": embedding
            }

            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/document_chunks",
                headers={
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal"
                },
                json=row
            )

            if response.status_code not in [200, 201, 204]:
                print(f"⚠️ Failed to insert chunk {i}: {response.text}", file=sys.stderr)

        print(f"✅ Stored {len(chunks)} chunks in Supabase", file=sys.stderr)

    except Exception as e:
        print(f"❌ Supabase storage error: {e}", file=sys.stderr)
        sys.exit(1)


def ingest_document(file_path: str, doc_id: str):
    """Main ingestion pipeline."""
    print(f"📄 Processing document: {file_path}", file=sys.stderr)

    # 1. Extract text
    text = extract_text(file_path)
    print(f"   Extracted {len(text)} characters", file=sys.stderr)

    # 2. Chunk text
    chunks = chunk_text(text)
    print(f"   Created {len(chunks)} chunks", file=sys.stderr)

    # 3. Get embeddings
    print("   Generating embeddings...", file=sys.stderr)
    embeddings = get_embeddings(chunks)

    # 4. Store in Supabase
    print("   Storing in Supabase...", file=sys.stderr)
    store_chunks_in_supabase(doc_id, chunks, embeddings)

    result = {
        "doc_id": doc_id,
        "chunks_created": len(chunks),
        "status": "success"
    }

    print(json.dumps(result))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest, chunk, embed, and store document")
    parser.add_argument("file_path", help="Path to document (PDF or TXT)")
    parser.add_argument("--doc_id", required=True, help="Document identifier")

    args = parser.parse_args()

    if not os.path.exists(args.file_path):
        print(f"❌ File not found: {args.file_path}")
        sys.exit(1)

    ingest_document(args.file_path, args.doc_id)
