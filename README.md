# Video Intelligence Plugin

> Real-time video call intelligence tool for transcription, document analysis, and adversarial insights.

## 🎯 Goal

Build a tool that:
- Ingests YouTube videos with multiple speakers (e.g., interviews, debates)
- Performs real-time transcription + speaker attribution
- Accepts user-uploaded documents
- Surfaces document-relevant content as speakers talk
- After video ends, runs adversarial analysis:
  - Cross-checks transcript vs uploaded docs (coherence)
  - Detects tone shifts (e.g., lying, evasion)
  - Produces a strategic adversarial summary of the interaction

---

## 🧩 Core Modules

### 1. Video Ingestion
- Download and process YouTube videos (mp4 or audio only)
- Support arbitrary general-purpose videos (not just Zoom)
- Extract clear audio even from dynamic scenes

**Tech:** `yt-dlp`, `ffmpeg`

### 2. Real-Time Transcription + Speaker Diarization
- Transcribe audio as it plays
- Attribute speech to Speaker A, B, C (as applicable)
- Store timestamps and speaker segments

**Tech:** `whisperx` (preferred), fallback to `whisper` + `pyannote`

### 3. Document Ingestion + Chunking
- User uploads 1+ reference documents (PDF or text)
- Documents are chunked and embedded for semantic search
- Indexed in local or Supabase vector store

**Tech:** `pdfplumber` or `PyMuPDF`, OpenAI embeddings, `pgvector`, Supabase

### 4. Live Semantic Context Box
As transcription occurs:
- Extract keywords or phrases from speech
- Run embedding search to find matching doc chunks
- Surface relevant chunks live in a side panel or console

**Tech:** Keyword extraction (`KeyBERT`, `RAKE`, or naïve n-grams), top-k cosine similarity using `pgvector`

### 5. Post-Convo Adversarial Pass
Run immediately after transcription is complete:

#### a. Coherence Check
- Does transcript refer to facts or events contradicted by uploaded docs?
- Flag mismatches or omissions

#### b. Tone/Deception Detection
- Identify tone shifts: evasiveness, hesitation, aggression
- Use heuristics or OpenAI prompt engineering

#### c. Adversarial Summary
Strategic distillation:
- Hidden goals
- Deception attempts
- Conflict or alignment of interests

**Tech:** GPT-4o (chat completion with transcript + docs), custom heuristics for tone flags

---

## ✅ Acceptance Criteria

### General

| ID  | Criteria |
|-----|----------|
| AC1 | System can ingest and transcribe any public YouTube video with at least 2 speakers |
| AC2 | User can upload at least one document (`.pdf` or `.txt`) prior to transcription |
| AC3 | All major events in the transcription are timestamped and speaker-attributed |

### Live Context Box

| ID  | Criteria |
|-----|----------|
| AC4 | Keywords/phrases from the transcript are extracted in real time |
| AC5 | Matching document chunks are retrieved and shown in a live "context box" |
| AC6 | Only the most relevant chunk (or top-3) is surfaced at any time |

### Adversarial Analysis

| ID   | Criteria |
|------|----------|
| AC7  | System flags contradictions between speech and uploaded docs (coherence test) |
| AC8  | System detects tone shifts based on predefined linguistic cues |
| AC9  | A summary is generated that adversarially explains what happened and why it matters |
| AC10 | Summary highlights strategic lies, manipulation, or intent mismatches between speakers |

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- **Python 3.11** (required - Python 3.12+ not supported due to PyTorch/numba compatibility)
- `yt-dlp` (`brew install yt-dlp`)
- `ffmpeg` (`brew install ffmpeg`)
- OpenAI API key
- Supabase account

### Installation

```bash
# Clone the repo
git clone https://github.com/EvanGrandfield1/video-intelligence-plugin.git
cd video-intelligence-plugin

# Install Node dependencies
npm install

# Set up Python environment (must use Python 3.11)
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Supabase Setup

Run this SQL in your Supabase SQL editor:

```sql
-- Enable pgvector extension
-- Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Drop existing table if it has wrong schema
DROP TABLE IF EXISTS document_chunks;

-- Create document chunks table with correct schema
CREATE TABLE document_chunks (
  id BIGSERIAL PRIMARY KEY,
  doc_id TEXT NOT NULL,
  chunk_index INTEGER NOT NULL,
  content TEXT NOT NULL,
  embedding VECTOR(1536),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create the RPC function for vector similarity search
CREATE OR REPLACE FUNCTION match_doc_chunks(
  query_embedding VECTOR(1536),
  match_count INT DEFAULT 3,
  filter_doc_id TEXT DEFAULT NULL
)
RETURNS TABLE (
  id BIGINT,
  doc_id TEXT,
  chunk_index INT,
  content TEXT,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    dc.id,
    dc.doc_id,
    dc.chunk_index,
    dc.content,
    1 - (dc.embedding <=> query_embedding) AS similarity
  FROM document_chunks dc
  WHERE (filter_doc_id IS NULL OR dc.doc_id = filter_doc_id)
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
```

### Run

```bash
npm run dev
```

---

## 📁 Project Structure

```
├── index.ts                      # Main pipeline orchestrator
├── app/
│   ├── ingest/
│   │   ├── youtubeIngest.ts      # YouTube audio download
│   │   └── transcribe_diarize.py # Whisper transcription
│   ├── documents/
│   │   ├── uploadDocument.ts     # Document upload API
│   │   └── doc_ingest_chunk_embed.py
│   ├── context-box/
│   │   ├── runLiveContextBox.ts  # Node wrapper
│   │   └── live_context_box.py   # Keyword extraction & search
│   └── post-analysis/
│       └── adversarial_analysis.py
├── data/
│   ├── audio/                    # Downloaded audio files
│   ├── docs/                     # Uploaded documents
│   └── transcripts/              # Generated transcripts
├── requirements.txt              # Python dependencies
└── .env.example                  # Environment template
```

---

## 📄 License

ISC



