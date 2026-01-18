// index.ts
import { downloadYouTubeAudio } from "./app/ingest/youtubeIngest";

(async () => {
  const url = "https://www.youtube.com/watch?v=xEuRznnu5YI";
  const wavPath = await downloadYouTubeAudio(url);
  console.log("✅ Audio extracted to:", wavPath);
})();
