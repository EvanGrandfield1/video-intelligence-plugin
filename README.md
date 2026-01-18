# Video Intelligence Plugin

## How to Use

1. Clone the repository:

   ```bash
   git clone https://github.com/EvanGrandfield1/video-intelligence-plugin.git
   cd video-intelligence-plugin
   ```

2. Install Node.js dependencies:

   ```bash
   npm install
   ```

3. Set up Python environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. Configure environment variables:

   ```bash
   cp .env.example .env  # Then fill in API keys
   ```

5. Start the development server:

   ```bash
   npm run dev
   ```

---

## SPEC: Real-Time Video Call Intelligence Plugin (MVP)

### Goal

Build a tool that:

- Ingests YouTube videos with multiple speakers (e.g., interviews, debates)
- Performs real-time transcription + speaker attribution
- Accepts user-uploaded documents
- Surfaces document-relevant content as speakers talk
- After video ends, runs adversarial analysis:
  - Cross-checks transcript vs uploaded docs (coherence)
  - Detects tone shifts (e.g. lying, evasion)
  - Produces a strategic adversarial summary of the interaction

### Core Modules

#### 1. Video Ingestion

- Download and process YouTube videos (mp4 or audio only)
- Support arbitrary general-purpose videos (not just Zoom)
- Extract clear audio even from dynamic scenes
- **Tech:** yt-dlp, ffmpeg

#### 2. Real-Time Transcription + Speaker Diarization

- Transcribe audio as it plays
- Attribute speech to Speaker A, B, C (as applicable)
- Store timestamps and speaker segments
- **Tech:** whisperx (preferred), fallback to whisper + pyannote

#### 3. Document Ingestion + Chunking

- User uploads 1+ reference documents (PDF or text)
- Documents are chunked and embedded for semantic search
- Indexed in local or Supabase vector store
- **Tech:** pdfplumber or PyMuPDF, OpenAI embeddings, pgvector, Supabase

#### 4. Live Semantic Context Box

As transcription occurs:

- Extract keywords or phrases from speech
- Run embedding search to find matching doc chunks
- Surface relevant chunks live in a side panel or console
- **Tech:** keyword extraction (KeyBERT, RAKE, or naïve n-grams), top-k cosine
  similarity using pgvector

#### 5. Post-Convo Adversarial Pass

Run immediately after transcription is complete:

##### a. Coherence Check

- Does transcript refer to facts or events contradicted by uploaded docs?
- Flag mismatches or omissions

##### b. Tone/Deception Detection

- Identify tone shifts: evasiveness, hesitation, aggression
- Use heuristics or OpenAI prompt engineering

##### c. Adversarial Summary

Strategic distillation:

- Hidden goals
- Deception attempts
- Conflict or alignment of interests
- **Tech:** GPT-4 (chat completion with transcript + docs), custom heuristics
  for tone flags

---

## ACCEPTANCE CRITERIA

### General

| ID  | Criteria                                                                      |
| --- | ----------------------------------------------------------------------------- |
| AC1 | System can ingest and transcribe any public YouTube video with at least 2 speakers |
| AC2 | User can upload at least one document (.pdf or .txt) prior to transcription  |
| AC3 | All major events in the transcription are timestamped and speaker-attributed |

### Live Context Box

| ID  | Criteria                                                                    |
| --- | --------------------------------------------------------------------------- |
| AC4 | Keywords/phrases from the transcript are extracted in real time             |
| AC5 | Matching document chunks are retrieved and shown in a live "context box"    |
| AC6 | Only the most relevant chunk (or top-3) is surfaced at any time            |

### Adversarial Analysis

| ID   | Criteria                                                                           |
| ---- | ---------------------------------------------------------------------------------- |
| AC7  | System flags contradictions between speech and uploaded docs (coherence test)     |
| AC8  | System detects tone shifts based on predefined linguistic cues                    |
| AC9  | A summary is generated that adversarially explains what happened and why it matters |
| AC10 | Summary highlights strategic lies, manipulation, or intent mismatches between speakers |
