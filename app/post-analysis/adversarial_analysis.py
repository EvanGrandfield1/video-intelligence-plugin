#!/usr/bin/env python3
"""
Adversarial Analysis: Post-conversation analysis including
coherence check, tone/deception detection, and adversarial summary.
"""
import argparse
import json
import os
import sys
from typing import List, Dict

from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")


def load_transcript(transcript_path: str) -> List[Dict]:
    """Load transcript JSON."""
    with open(transcript_path, "r") as f:
        data = json.load(f)
    return data.get("segments", [])


def get_document_chunks(doc_id: str) -> List[str]:
    """Retrieve document chunks from Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []

    import requests

    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/document_chunks",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
        },
        params={
            "doc_id": f"eq.{doc_id}",
            "select": "content",
            "order": "chunk_index"
        }
    )

    if response.status_code == 200:
        return [chunk["content"] for chunk in response.json()]
    return []


def format_transcript(segments: List[Dict]) -> str:
    """Format transcript segments into readable text."""
    lines = []
    for seg in segments:
        speaker = seg.get("speaker", "UNKNOWN")
        text = seg.get("text", "")
        start = seg.get("start", 0)
        lines.append(f"[{start:.1f}s] {speaker}: {text}")
    return "\n".join(lines)


def call_openai(system_prompt: str, user_prompt: str) -> str:
    """Call OpenAI API for analysis."""
    if not OPENAI_API_KEY:
        return "❌ OPENAI_API_KEY not set"

    import requests

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 2000
        }
    )

    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def coherence_analysis(transcript_text: str, doc_text: str) -> Dict:
    """Check coherence between transcript claims and document content."""
    system_prompt = """You are an expert analyst checking for coherence and consistency.
    Compare the transcript against the reference documents and identify:
    1. Claims that are SUPPORTED by the documents
    2. Claims that CONTRADICT the documents
    3. Claims that are UNSUPPORTED (neither confirmed nor denied)
    
    Be specific and cite examples."""

    user_prompt = f"""TRANSCRIPT:
{transcript_text}

REFERENCE DOCUMENTS:
{doc_text}

Analyze the coherence between the transcript and documents."""

    result = call_openai(system_prompt, user_prompt)
    return {"type": "coherence", "analysis": result}


def tone_deception_analysis(transcript_text: str) -> Dict:
    """Analyze tone and detect potential deception indicators."""
    system_prompt = """You are an expert in communication analysis and behavioral psychology.
    Analyze the transcript for:
    1. Overall tone (confident, evasive, aggressive, defensive, etc.)
    2. Potential deception indicators (hedging language, inconsistencies, deflection)
    3. Emotional shifts throughout the conversation
    4. Power dynamics between speakers
    
    Note: This is analytical, not accusatory. Flag patterns, not conclusions."""

    user_prompt = f"""TRANSCRIPT:
{transcript_text}

Provide a detailed tone and behavioral analysis."""

    result = call_openai(system_prompt, user_prompt)
    return {"type": "tone_deception", "analysis": result}


def adversarial_summary(transcript_text: str, doc_text: str) -> Dict:
    """Generate adversarial summary highlighting concerns and gaps."""
    system_prompt = """You are a critical analyst preparing a devil's advocate summary.
    Your job is to:
    1. Summarize the key points of the conversation
    2. Highlight potential weaknesses in arguments made
    3. Identify missing information or gaps
    4. List follow-up questions that should be asked
    5. Note any red flags or areas requiring verification
    
    Be thorough but fair. The goal is due diligence, not character assassination."""

    user_prompt = f"""TRANSCRIPT:
{transcript_text}

REFERENCE DOCUMENTS:
{doc_text}

Generate an adversarial analysis summary."""

    result = call_openai(system_prompt, user_prompt)
    return {"type": "adversarial_summary", "analysis": result}


def run_full_analysis(transcript_path: str, doc_id: str = None):
    """Run complete adversarial analysis pipeline."""
    print("🔍 Starting Adversarial Analysis...", file=sys.stderr)

    # Load transcript
    segments = load_transcript(transcript_path)
    transcript_text = format_transcript(segments)
    print(f"   Loaded {len(segments)} transcript segments", file=sys.stderr)

    # Load documents if doc_id provided
    doc_text = ""
    if doc_id:
        chunks = get_document_chunks(doc_id)
        doc_text = "\n\n".join(chunks)
        print(f"   Loaded {len(chunks)} document chunks", file=sys.stderr)

    results = {
        "transcript_segments": len(segments),
        "doc_chunks": len(chunks) if doc_id else 0,
        "analyses": []
    }

    # Run analyses
    print("   Running coherence analysis...", file=sys.stderr)
    results["analyses"].append(coherence_analysis(transcript_text, doc_text))

    print("   Running tone/deception analysis...", file=sys.stderr)
    results["analyses"].append(tone_deception_analysis(transcript_text))

    print("   Generating adversarial summary...", file=sys.stderr)
    results["analyses"].append(adversarial_summary(transcript_text, doc_text))

    print("✅ Adversarial Analysis Complete", file=sys.stderr)
    print(json.dumps(results, indent=2))

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Adversarial Analysis")
    parser.add_argument("transcript_path", help="Path to transcript JSON")
    parser.add_argument("--doc_id", help="Document ID for reference (optional)")

    args = parser.parse_args()

    if not os.path.exists(args.transcript_path):
        print(f"❌ Transcript not found: {args.transcript_path}")
        sys.exit(1)

    run_full_analysis(args.transcript_path, args.doc_id)
