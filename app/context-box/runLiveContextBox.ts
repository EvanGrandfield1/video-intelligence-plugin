// app/context-box/runLiveContextBox.ts
import path from "path";
import { execSync } from "child_process";

export async function runLiveContextBox(transcriptPath: string, docId: string, topN: number = 3): Promise<any[]> {
    const pyScript = path.join(__dirname, "live_context_box.py");
    const command = `python3 \"${pyScript}\" \"${transcriptPath}\" --doc_id \"${docId}\" --top_n ${topN}`;
    try {
        console.log(`Running live context box for transcript: ${transcriptPath}, doc: ${docId}`);
        const result = execSync(command, { encoding: "utf-8" });
        // Each segment's output is a JSON object per line
        const outputs = result.trim().split(/\n(?={)/).map(line => JSON.parse(line));
        return outputs;
    } catch (err) {
        console.error("❌ Live context box failed:", err);
        throw err;
    }
}
