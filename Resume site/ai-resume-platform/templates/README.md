# ATS Resume Templates

Source designs imported from `D:\resumes`. Each PDF is matched to a live React preview component and shared style tokens in `lib/templates.ts`.

| Template ID | Source PDF | Preview Component |
|---|---|---|
| `blue-clean` | Blue and White Clean and Professional Resume (1).pdf | `BlueCleanTemplate.tsx` |
| `tech-pro` | White and Black Tech Professional Resume (1).pdf | `TechProTemplate.tsx` |
| `ats-friendly` | Black and White Professional ATS Friendly Resume.pdf | `AtsFriendlyTemplate.tsx` |
| `modern-bw` | Black and White Modern Professional Resume (1).pdf | `ModernBwTemplate.tsx` |
| `corporate-minimal` | White and Blue Minimalist Professional Corporate ATS Resume.pdf | `CorporateMinimalTemplate.tsx` |

PDFs are also served at `/templates/<filename>.pdf` for side-by-side comparison with the live preview.

To replace a design: drop a new PDF here, update tokens in `lib/templates.ts`, and adjust the matching component in `components/resume-templates/`.