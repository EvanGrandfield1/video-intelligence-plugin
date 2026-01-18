// app/documents/uploadDocument.ts
import fs from "fs";
import path from "path";
import { execSync } from "child_process";
import { Request, Response } from "express";

const DOCS_DIR = path.join(__dirname, "../../data/docs");
const PY_INGEST_PATH = path.join(__dirname, "doc_ingest_chunk_embed.py");

if (!fs.existsSync(DOCS_DIR)) fs.mkdirSync(DOCS_DIR, { recursive: true });

export async function handleDocumentUpload(req: Request, res: Response) {
    try {
        if (!req.file) {
            return res.status(400).json({ error: "No file uploaded" });
        }
        const file = req.file;
        const ext = path.extname(file.originalname).toLowerCase();
        if (ext !== ".pdf" && ext !== ".txt") {
            return res.status(400).json({ error: "Only PDF or TXT files supported" });
        }
        const savePath = path.join(DOCS_DIR, file.originalname);
        fs.writeFileSync(savePath, file.buffer);
        // Call Python backend for chunking/embedding/storage
        const command = `python3 \"${PY_INGEST_PATH}\" \"${savePath}\" --doc_id \"${file.originalname}\"`;
        const result = execSync(command, { encoding: "utf-8" });
        res.json({ success: true, result: JSON.parse(result) });
    } catch (err) {
        console.error("❌ Document upload/ingest failed:", err);
        res.status(500).json({ error: "Document ingestion failed" });
    }
}
