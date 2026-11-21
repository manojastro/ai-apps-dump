import fs from "node:fs";
import path from "node:path";
import { pdf } from "pdf-to-img";
const projectRoot = process.cwd();
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
  const doc = await pdf(file, { scale: 1.4 });
  let p = 0;
  for await (const image of doc) {
    p++;
    const safe = rel.replace(/[^a-z0-9]+/gi, "-").replace(/(^-|-$)/g, "");
    fs.writeFileSync(path.join(outDir, `${String(i).padStart(2,"0")}-${safe}-p${p}.png`), image);
    if (p >= 6) break;
  }
  console.log(rel, p);
}
