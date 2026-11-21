import { NextRequest, NextResponse } from "next/server";
import mammoth from "mammoth";
import { extractPdfText } from "@/lib/pdfParse";

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const file = formData.get("file") as File | null;

    if (!file) {
      return NextResponse.json({ error: "No file provided" }, { status: 400 });
    }

    const buffer = Buffer.from(await file.arrayBuffer());
    const name = file.name.toLowerCase();

    let text = "";

    if (name.endsWith(".docx")) {
      const result = await mammoth.extractRawText({ buffer });
      text = result.value;
    } else if (name.endsWith(".pdf")) {
      text = await extractPdfText(buffer);
    } else {
      return NextResponse.json(
        { error: "Unsupported file type. Use .docx or .pdf" },
        { status: 400 }
      );
    }

    if (!text.trim()) {
      return NextResponse.json(
        { error: "Could not extract text from the file" },
        { status: 422 }
      );
    }

    return NextResponse.json({ text });
  } catch (e) {
    console.error("Resume parse error:", e);
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Parse failed" },
      { status: 500 }
    );
  }
}