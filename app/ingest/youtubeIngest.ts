// app/ingest/youtubeIngest.ts
import { execSync } from "child_process";
import fs from "fs";
import path from "path";

const AUDIO_DIR = path.join(__dirname, "../../data/audio");

export async function downloadYouTubeAudio(youtubeUrl: string): Promise<string> {
  if (!fs.existsSync(AUDIO_DIR)) fs.mkdirSync(AUDIO_DIR, { recursive: true });

  const videoId = youtubeUrl.split("v=")[1]?.split("&")[0] || Date.now().toString();
  const outputPath = path.join(AUDIO_DIR, `${videoId}.wav`);

  const command = `yt-dlp -x --audio-format wav --output "${AUDIO_DIR}/${videoId}.%(ext)s" "${youtubeUrl}"`;

  try {
    console.log(`Downloading and extracting audio from: ${youtubeUrl}`);
    execSync(command, { stdio: "inherit" });
    return outputPath;
  } catch (err) {
    console.error("❌ Failed to download audio:", err);
    throw err;
  }
}

