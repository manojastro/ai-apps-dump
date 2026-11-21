# CareerForge AI

AI-powered **ATS resume builder** + **job market trends portal** + **AI career chatbot**.

## Features
- **Resume Builder**: type your skills, or upload an old resume (PDF / DOCX / TXT). Claude rewrites it into a single-column, ATS-friendly resume with an ATS score, matched/missing keywords and tips. You can edit the text on the page, then export to PDF (print) or Word (.doc). Paste a job description to tailor the keywords to it.
- **Job Trends**: openings by city, top 10 domains, top 10 highest-paying domains, fastest-growing domains, plus ranked lists for trending, top-paid and easy-entry roles and the top 10 roles for freshers and for experienced people. Includes a domain explorer and a city table.
- **AI Career Chat**: ask "which domain should I pick?" and get answers based on the trends data.
- **Demo mode**: with no API key the app still runs. It builds resumes from a template and the chatbot answers from rules, so you can show it off without a key.

## Run
```bash
npm install
cp .env.example .env   # optional: put ANTHROPIC_API_KEY here
npm start              # http://localhost:3000
```
You can also paste an API key in the app's **Settings**. It is stored in your browser only.

## AI providers
- **Claude (Anthropic)**: the default. Reads uploaded PDFs directly and guarantees the resume format (structured outputs).
- **DeepSeek via APInex**, or any other OpenAI-compatible API: set `OPENAI_API_KEY` (plus `OPENAI_BASE_URL` / `OPENAI_MODEL` to change them), or choose it in the app's Settings. These models read text only, so PDFs are converted to text on the server, and the server checks and repairs the AI's resume JSON itself.

APInex is a third-party reseller, so any resume details you enter are sent to it.

## Protecting your API key
If you set `ANTHROPIC_API_KEY` on the server, visitors who don't bring their own key use yours. To stop a public link from draining it, the server limits that usage:
- `LIMIT_RESUME_PER_HOUR` (default 5) and `LIMIT_CHAT_PER_HOUR` (default 30) per visitor
- `LIMIT_DAILY_TOTAL` (default 300) AI requests per day across everyone
- `REQUIRE_USER_KEY=true` turns the shared key off completely

Visitors who paste their own key in Settings are never limited. The counters live in memory, so with several server instances each one counts separately.

## Notes
- The model defaults to `claude-opus-5-5`. You can change it with `ANTHROPIC_MODEL` in `.env`.
- The job data in `data/jobs.json` is an **indicative sample snapshot** (India, INR LPA). To show real numbers, swap it for a live jobs API such as Adzuna or a Naukri/LinkedIn data feed.
- The resume template lives in `renderResume()` in `public/app.js` and the `.r-*` styles in `public/styles.css`. Swap it for your own ATS template there.

## Stack
Node.js + Express, Anthropic SDK, Mammoth (reads DOCX), Chart.js. Claude reads PDFs directly.
