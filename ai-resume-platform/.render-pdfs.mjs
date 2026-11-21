import fs from "node:fs";
import path from "node:path";
import { createCanvas, Path2D, DOMMatrix, ImageData } from "canvas";
globalThis.Path2D = Path2D;
globalThis.DOMMatrix = DOMMatrix;
globalThis.ImageData = ImageData;

const projectRoot = "D:/ai apps dump/ai-resume-platform";
const docs = await import(new URL("./node_modules/pdfjs-dist/legacy/build/pdf.mjs", import.meta.url).href);
const { getDocument } = docs;

const files = [
  "Best 1.pdf",
  "Best%202.pdf",
  "Black and White Minimalist Accountant Resume.pdf",
  "Black and White Simple Infographic Resume.pdf",
  "Black White Corporate Finance Resume.pdf",
  "public/templates/Black and White Modern Professional Resume (1).pdf",
  "public/templates/Black and White Professional ATS Friendly Resume.pdf",
  "public/templates/Blue and White Clean and Professional Resume (1).pdf",
  "public/templates/White and Black Tech Professional Resume (1).pdf",
  "public/templates/White and Blue Minimalist Professional Corporate ATS Resume.pdf",
];

const outDir = "C:/Users/manoj/AppData/Local/Temp/opencode/resume-refs";
fs.mkdirSync(outDir, { recursive: true });

for (const [i, rel] of files.entries()) {
  const file = path.resolve(projectRoot, rel);
  if (!fs.existsSync(file)) { console.log("MISSING", rel); continue; }
  const data = new Uint8Array(fs.readFileSync(file));
  const pdf = await getDocument({ data, verbosity: 0 }).promise;
  console.log(rel, "pages:", pdf.numPages);
  for (let p = 1; p <= Math.min(pdf.numPages, 6); p++) {
    const page = await pdf.getPage(p);
    const viewport = page.getViewport({ scale: 1.35 });
    const canvas = createCanvas(Math.ceil(viewport.width), Math.ceil(viewport.height));
    const ctx = canvas.getContext("2d");
    await page.render({ canvasContext: ctx, viewport, canvas }).promise;
    const safe = rel.replace(/[^a-z0-9]+/gi, "-").replace(/(^-|-$)/g, "");
    fs.writeFileSync(path.join(outDir, `${String(i).padStart(2, "0")}-${safe}-p${p}.png`), canvas.toBuffer("image/png"));
  }
}
console.log("done");


