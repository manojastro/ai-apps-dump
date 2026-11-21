import { NextRequest, NextResponse } from "next/server";
import { generateDocx } from "@/lib/docxExport";
import { getTemplate } from "@/lib/templates";
import type { ResumeData, TemplateId } from "@/lib/resumeSchema";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { resume, templateId } = body as {
      resume: ResumeData;
      templateId: TemplateId;
    };

    if (!resume) {
      return NextResponse.json({ error: "resume data is required" }, { status: 400 });
    }

    const style = getTemplate(templateId);
    const buffer = await generateDocx(resume, style);

    const filename = `${resume.personalInfo.fullName || "Resume"}_Resume.docx`;

    return new NextResponse(new Uint8Array(buffer), {
      headers: {
        "Content-Type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "Content-Disposition": `attachment; filename="${filename}"`,
      },
    });
  } catch (e) {
    console.error("Resume export error:", e);
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Export failed" },
      { status: 500 }
    );
  }
}