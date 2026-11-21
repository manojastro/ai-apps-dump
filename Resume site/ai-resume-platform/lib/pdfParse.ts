import path from "path";
import { pathToFileURL } from "url";

let workerConfigured = false;

async function ensurePdfWorker() {
  if (workerConfigured) return;
  const { PDFParse } = await import("pdf-parse");
  const workerPath = path.join(
    process.cwd(),
    "node_modules/pdf-parse/dist/pdf-parse/esm/pdf.worker.mjs"
  );
  PDFParse.setWorker(pathToFileURL(workerPath).href);
  workerConfigured = true;
}

export async function extractPdfText(buffer: Buffer): Promise<string> {
  await ensurePdfWorker();
  const { PDFParse } = await import("pdf-parse");
  const parser = new PDFParse({ data: buffer });
  try {
    const result = await parser.getText();
    return result.text;
  } finally {
    await parser.destroy();
  }
}