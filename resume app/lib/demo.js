// Offline "demo mode" used when no LLM API key is configured, so the portal still works
// end-to-end (e.g. for a LinkedIn walkthrough). Real AI output requires an API key.

const splitList = (s = "") =>
  s.split(/[,\n;|]/).map((x) => x.trim()).filter(Boolean);

const CATEGORY_HINTS = [
  ["Languages", /^(python|java|javascript|typescript|c\+\+|c#|c|go|rust|kotlin|swift|sql|r|php|ruby|scala)$/i],
  ["Frameworks & Libraries", /(react|angular|vue|next|node|express|django|flask|fastapi|spring|pytorch|tensorflow|pandas|numpy|langchain|flutter)/i],
  ["Cloud & DevOps", /(aws|azure|gcp|docker|kubernetes|terraform|jenkins|ci\/cd|linux|git)/i],
  ["Data & Tools", /(power ?bi|tableau|excel|spark|airflow|snowflake|bigquery|mongodb|postgres|mysql|figma|jira)/i],
];

function groupSkills(skills) {
  const groups = new Map();
  for (const s of skills) {
    const hit = CATEGORY_HINTS.find(([, re]) => re.test(s));
    const cat = hit ? hit[0] : "Core Skills";
    if (!groups.has(cat)) groups.set(cat, []);
    groups.get(cat).push(s);
  }
  return [...groups].map(([category, items]) => ({ category, items }));
}

// Skills may be typed as free text ("I know Python and SQL. Good at Excel"), so split on
// sentence breaks and "and" too, then drop filler words.
const parseSkills = (s = "") =>
  [...new Set(
    s.split(/[,\n;|]|\.(?:\s|$)|\band\b|\b(?:also|plus|with)\b/i)
      .map((x) => x.replace(/^\s*(i\s+(?:know|am good at|can|have)|good at|skilled in|experience (?:in|with)|familiar with|knowledge of)\s+/i, "").trim())
      .filter((x) => x && x.split(/\s+/).length <= 4)
  )];

export function buildDemoResume(f = {}) {
  const skills = parseSkills(f.skills);
  const role = f.targetRole || "Software Engineer";
  const top = skills.slice(0, 3).join(", ") || "modern technologies";
  const notes = splitList(f.notes).slice(0, 5);
  const fresher = /fresh|entry|student/i.test(f.level || "");

  return {
    name: f.name || "Your Name",
    title: role,
    contact: {
      email: f.email || "you@email.com",
      phone: f.phone || "+91 90000 00000",
      location: f.location || "India",
      linkedin: f.linkedin || "",
      github: f.github || "",
      portfolio: "",
    },
    summary: `${fresher ? "Motivated" : "Results-driven"} ${role} with hands-on expertise in ${top}. Skilled at building reliable, user-focused solutions, collaborating in agile teams and learning fast. Seeking to deliver measurable impact as a ${role}.`,
    skills: groupSkills(skills.length ? skills : ["Problem Solving", "Communication", "Teamwork"]),
    experience: fresher
      ? []
      : [
          {
            role,
            company: "Company Name",
            location: f.location || "",
            start: "2023",
            end: "Present",
            bullets: notes.length
              ? notes.map((n) => n.replace(/^./, (c) => c.toUpperCase()))
              : [
                  `Built and shipped features using ${top}, improving delivery speed by ~20%.`,
                  "Collaborated with cross-functional teams to gather requirements and deliver on schedule.",
                  "Wrote clean, tested code and participated in code reviews to raise quality.",
                ],
          },
        ],
    projects: [
      {
        name: `${role} Portfolio Project`,
        tech: skills.slice(0, 4).join(", "),
        bullets: [
          `Designed and developed an end-to-end project applying ${top}.`,
          "Documented architecture and deployed it publicly with a live demo link.",
        ],
      },
    ],
    education: [{ degree: "Bachelor's Degree", institution: "Your University", year: "", details: "" }],
    certifications: [],
    achievements: [],
    ats: {
      score: Math.min(90, 55 + skills.length * 3),
      matchedKeywords: skills.slice(0, 8),
      missingKeywords: [],
      tips: [
        "DEMO MODE: add an API key in Settings for a fully AI-written, tailored resume.",
        "Add measurable results (%, ₹, users, time saved) to every bullet.",
        "Paste the target job description to tailor keywords.",
      ],
    },
  };
}

export function demoChatReply(question, jobs) {
  const q = question.toLowerCase();
  const fmt = (arr, f) => arr.map((x, i) => `${i + 1}. ${f(x)}`).join("\n");
  const prefix = "_(Demo mode — add an API key in Settings for full AI answers.)_\n\n";

  if (/fresher|entry|beginner|graduate/.test(q))
    return prefix + "**Top in-demand roles for freshers:**\n" + fmt(jobs.freshers, (j) => `**${j.role}** — ${j.openings.toLocaleString("en-IN")} openings, ~₹${j.avgLPA} LPA`);
  if (/easy|quick|fast|switch|without coding|non.?tech/.test(q))
    return prefix + "**Easiest roles to break into:**\n" + fmt(jobs.easyEntry, (j) => `**${j.role}** — ~${j.learnMonths} months to learn, ~₹${j.fresherLPA} LPA start`);
  if (/high|pay|salary|money|highest/.test(q))
    return prefix + "**Top high-paying roles:**\n" + fmt(jobs.highPaying, (j) => `**${j.role}** — ₹${j.minLPA}–${j.maxLPA} LPA`);
  if (/city|cities|location|where/.test(q))
    return prefix + "**Cities by openings:**\n" + fmt([...jobs.cities].sort((a, b) => b.openings - a.openings).slice(0, 8), (c) => `**${c.name}** — ${c.openings.toLocaleString("en-IN")} openings, avg ₹${c.avgSalaryLPA} LPA`);
  if (/experienc|senior/.test(q))
    return prefix + "**Top roles for experienced professionals:**\n" + fmt(jobs.experienced, (j) => `**${j.role}** — ~₹${j.avgLPA} LPA`);

  const d = jobs.domains.find((x) => q.includes(x.name.toLowerCase().split(" ")[0]));
  if (d)
    return prefix + `**${d.name}**\n- Openings: ${d.openings.toLocaleString("en-IN")}\n- Fresher: ~₹${d.fresherLPA} LPA · Experienced: ~₹${d.experiencedLPA} LPA\n- Growth: +${d.growth}% YoY\n- Key skills: ${d.skills.join(", ")}\n- Roles: ${d.roles.join(", ")}`;

  return prefix + "**Trending jobs right now:**\n" + fmt(jobs.trendingJobs, (j) => `**${j.role}** — +${j.growth}% growth, ~₹${j.avgSalaryLPA} LPA`) +
    "\n\nAsk me about freshers, high-paying roles, easy-entry jobs, cities, or a domain like *Cloud* or *Data*.";
}
