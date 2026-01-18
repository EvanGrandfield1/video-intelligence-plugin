// index.ts
import { execSync } from "child_process";
import { downloadYouTubeAudio } from "./app/ingest/youtubeIngest";
import { handleDocumentUpload } from "./app/documents/uploadDocument";
import { runLiveContextBox } from "./app/context-box/runLiveContextBox";
import path from "path";
import fs from "fs";

(async () => {
  try {
    // 1. Download YouTube audio
    const url = "https://www.youtube.com/watch?v=xEuRznnu5YI";
    console.log("🎬 Step 1: Downloading YouTube audio...");
    const wavPath = await downloadYouTubeAudio(url);
    console.log("✅ Audio extracted to:", wavPath);

    // 2. Transcribe and diarize (call Python script)
    console.log("\n🎙️ Step 2: Transcribing and diarizing...");
    const transcriptPath = path.join(__dirname, "data/transcripts/transcript.json");
    const transcriptDir = path.dirname(transcriptPath);
    if (!fs.existsSync(transcriptDir)) fs.mkdirSync(transcriptDir, { recursive: true });

    const diarizeScript = path.join(__dirname, "app/ingest/transcribe_diarize.py");
    const diarizeCmd = `python3 "${diarizeScript}" "${wavPath}" --output "${transcriptPath}"`;
    execSync(diarizeCmd, { stdio: "inherit" });
    console.log("✅ Transcript generated:", transcriptPath);

    // 3. Document upload and chunking
    console.log("\n📄 Step 3: Processing documents...");
    const docFilePath = path.join(__dirname, "data/docs/test_doc.txt");
    const docDir = path.dirname(docFilePath);
    if (!fs.existsSync(docDir)) fs.mkdirSync(docDir, { recursive: true });

    if (!fs.existsSync(docFilePath)) {
      fs.writeFileSync(docFilePath, "This is a test document for semantic search. Add more content as needed.");
    }

    // Simulate Express req/res for upload
    const req: any = { file: { originalname: "test_doc.txt", buffer: fs.readFileSync(docFilePath) } };
    const res: any = {
      status: (code: number) => ({ json: (obj: any) => console.log("   Document upload:", obj) }),
      json: (obj: any) => console.log("   Document upload:", obj)
    };
    await handleDocumentUpload(req, res);

    // 4. Live context box
    console.log("\n🔎 Step 4: Running live context box...");
    const docId = "test_doc.txt";
    const contextResults = await runLiveContextBox(transcriptPath, docId, 3);
    console.log("✅ Live Context Box Results:", JSON.stringify(contextResults, null, 2));

    // 5. Adversarial analysis
    console.log("\n🕵️ Step 5: Running adversarial analysis...");
    const advScript = path.join(__dirname, "app/post-analysis/adversarial_analysis.py");
    const advCmd = `python3 "${advScript}" "${transcriptPath}" --doc_id "${docId}"`;
    const advResult = execSync(advCmd, { encoding: "utf-8" });
    console.log("✅ Adversarial Analysis Result:", advResult);

    console.log("\n🎉 Pipeline complete!");
  } catch (err) {
    console.error("❌ Pipeline failed:", err);
    process.exit(1);
  }
})();
