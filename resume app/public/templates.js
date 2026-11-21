// ATS-friendly resume templates, modelled on the 4 strongest designs in the user's
// resume collection. All are single text flow (no photos, tables or text boxes) so ATS
// parsers read them in order. Each template = markup builder + scoped CSS.
//
// Every editable piece of text carries data-path="<field path>" so edits made on the page
// are written back into the resume data and survive template switches and refreshes.
(() => {
const esc = (s = "") => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

// One editable field. `list: true` means the text is a comma-separated array.
const F = (path, value, { tag = "span", cls = "", list = false } = {}) => {
  const text = Array.isArray(value) ? value.join(", ") : value ?? "";
  return `<${tag} class="${cls}" data-path="${path}"${list ? ' data-list="1"' : ""} contenteditable="true" spellcheck="false">${esc(text)}</${tag}>`;
};

const has = (x) => (typeof x === "string" ? x.trim() : x && Object.values(x).some((v) => (Array.isArray(v) ? v.length : String(v || "").trim())));
// keep original indexes so data-path points at the right array slot
const idx = (arr) => (arr || []).map((v, i) => [v, i]).filter(([v]) => has(v));
const bullets = (arr, base) => {
  const items = idx(arr);
  return items.length ? `<ul>${items.map(([b, i]) => F(`${base}.${i}`, b, { tag: "li" })).join("")}</ul>` : "";
};
const dates = (base, x) =>
  x.start || x.end ? `${F(`${base}.start`, x.start)}${x.start && x.end ? " - " : ""}${F(`${base}.end`, x.end)}` : "";

// ---------- shared section builders ----------
const S = {
  summary: (r) => (r.summary ? F("summary", r.summary, { tag: "p", cls: "t-p" }) : ""),

  skillsLines: (r) =>
    idx(r.skills).map(([s, i]) => `<div class="t-skill-line"><b>${F(`skills.${i}.category`, s.category)}:</b> ${F(`skills.${i}.items`, s.items || [], { list: true })}</div>`).join(""),
  skillsGrid: (r, cols) => {
    const items = idx(r.skills).flatMap(([s, i]) => (s.items || []).map((it, j) => [it, `skills.${i}.items.${j}`])).filter(([it]) => it);
    return items.length ? `<ul class="t-grid t-cols-${cols}">${items.map(([it, p]) => F(p, it, { tag: "li" })).join("")}</ul>` : "";
  },

  experience: (r, style) =>
    idx(r.experience).map(([x, i]) => {
      const b = `experience.${i}`;
      if (style === "elegant") {
        return `<div class="t-item"><div class="t-head"><b>${F(`${b}.role`, x.role)}</b>${x.start || x.end ? ` | <b>${dates(b, x)}</b>` : ""}</div>
          ${x.company ? `<div class="t-org">${F(`${b}.company`, x.company)}${x.location ? `, ${F(`${b}.location`, x.location)}` : ""}</div>` : ""}${bullets(x.bullets, `${b}.bullets`)}</div>`;
      }
      return `<div class="t-item"><div class="t-row"><span><b>${F(`${b}.role`, x.role)}${x.company ? `, ${F(`${b}.company`, x.company)}` : ""}</b>${x.location ? ` ${F(`${b}.location`, x.location, { cls: "t-loc" })}` : ""}</span>
        <span class="t-date">${dates(b, x)}</span></div>${bullets(x.bullets, `${b}.bullets`)}</div>`;
    }).join(""),

  projects: (r, style) =>
    idx(r.projects).map(([p, i]) => {
      const b = `projects.${i}`;
      if (style === "elegant") {
        return `<div class="t-item"><div class="t-head"><b>${F(`${b}.name`, p.name)}</b></div>${p.tech ? `<div class="t-org">${F(`${b}.tech`, p.tech)}</div>` : ""}${bullets(p.bullets, `${b}.bullets`)}</div>`;
      }
      return `<div class="t-item"><div><b>${F(`${b}.name`, p.name)}</b>${p.tech ? ` <span class="t-loc">| ${F(`${b}.tech`, p.tech)}</span>` : ""}</div>${bullets(p.bullets, `${b}.bullets`)}</div>`;
    }).join(""),

  education: (r, style) =>
    idx(r.education).map(([e, i]) => {
      const b = `education.${i}`;
      const details = e.details ? `<ul>${F(`${b}.details`, e.details, { tag: "li" })}</ul>` : "";
      if (style === "elegant") {
        return `<div class="t-item"><div class="t-head"><b>${F(`${b}.degree`, e.degree)}</b>${e.year ? ` | <b>${F(`${b}.year`, e.year)}</b>` : ""}</div>
          ${e.institution ? `<div class="t-org">${F(`${b}.institution`, e.institution)}</div>` : ""}${details}</div>`;
      }
      return `<div class="t-item"><div class="t-row"><span><b>${F(`${b}.degree`, e.degree)}</b></span><span class="t-date">${F(`${b}.year`, e.year)}</span></div>
        ${e.institution ? `<div>${F(`${b}.institution`, e.institution)}</div>` : ""}${details}</div>`;
    }).join(""),
};

const CONTACT_KEYS = ["email", "phone", "location", "linkedin", "github", "portfolio"];
const contactLine = (r) =>
  CONTACT_KEYS.filter((k) => r.contact?.[k]).map((k) => F(`contact.${k}`, r.contact[k])).join(" | ");

function sections(r, order, style, skills) {
  const map = {
    summary: ["Summary", S.summary(r)],
    skills: [style === "classic" ? "Key Skills" : style === "modern" ? "Technical Skills" : "Skills", skills(r)],
    experience: [style === "classic" ? "Work Experience" : "Professional Experience", S.experience(r, style)],
    projects: ["Projects", S.projects(r, style)],
    education: ["Education", S.education(r, style)],
    certifications: ["Certifications", bullets(r.certifications, "certifications")],
    achievements: [style === "elegant" ? "Notable Awards" : "Achievements", bullets(r.achievements, "achievements")],
  };
  return order
    .map((k) => map[k])
    .filter(([, body]) => body)
    .map(([title, body]) => `<section class="t-sec"><h2>${title}</h2><div class="t-body">${body}</div></section>`)
    .join("");
}

const header = (r) => `
  <header class="t-header">
    ${F("name", r.name, { tag: "h1", cls: "t-name" })}
    ${r.title ? F("title", r.title, { tag: "div", cls: "t-title" }) : ""}
    <div class="t-contact">${contactLine(r)}</div>
  </header>`;

// ---------- the 4 templates ----------
const TEMPLATES = {
  classic: {
    name: "Classic",
    desc: "Navy labels in a left column",
    swatch: "#1f4e8c",
    render: (r) => header(r) + sections(r, ["summary", "experience", "projects", "education", "skills", "certifications", "achievements"], "classic", (x) => S.skillsGrid(x, 2)),
    css: `
      .tpl-classic{font-family:"Helvetica Neue",Arial,sans-serif;font-size:10pt;line-height:1.4;color:#222}
      .tpl-classic .t-name{font-size:24pt;font-weight:800;color:#1f4e8c;margin:0;letter-spacing:.3px}
      .tpl-classic .t-title{font-size:11pt;font-weight:600;color:#333;margin-top:2px}
      .tpl-classic .t-contact{font-size:9pt;color:#333;margin-top:3px;padding-bottom:10px;border-bottom:2px solid #1f4e8c}
      .tpl-classic .t-sec{display:grid;grid-template-columns:120px 1fr;gap:16px;padding:12px 0;border-bottom:1px solid #8aa6cf}
      .tpl-classic .t-sec:last-child{border-bottom:0}
      .tpl-classic .t-sec h2{font-size:10.5pt;font-weight:800;color:#1f4e8c;text-transform:uppercase;margin:0;line-height:1.3}
      .tpl-classic .t-p{margin:0;text-align:justify}`,
  },

  elegant: {
    name: "Elegant",
    desc: "Centered serif name, teal accents",
    swatch: "#2a8a74",
    render: (r) => {
      const c = r.contact || {};
      const col = (label, key) => (c[key] ? `<div><b>${label}:</b><br>${F(`contact.${key}`, c[key])}</div>` : "");
      const links = ["linkedin", "github", "portfolio"].filter((k) => c[k]).map((k) => F(`contact.${k}`, c[k])).join(" | ");
      return `
      <header class="t-header">
        ${F("name", r.name, { tag: "h1", cls: "t-name" })}
        ${r.title ? F("title", r.title, { tag: "div", cls: "t-title" }) : ""}
        <div class="t-rule"></div>
        ${r.summary ? `<h2 class="t-sum-h">Professional Summary</h2>${F("summary", r.summary, { tag: "p", cls: "t-sum" })}` : ""}
        <div class="t-contact">${col("Phone", "phone")}${col("Email", "email")}${col("Address", "location")}</div>
        ${links ? `<div class="t-links">${links}</div>` : ""}
      </header>
      ${sections(r, ["education", "experience", "projects", "skills", "certifications", "achievements"], "elegant", S.skillsLines)}
      <div class="t-rule t-end"></div>`;
    },
    css: `
      .tpl-elegant{font-family:"Open Sans",Calibri,Arial,sans-serif;font-size:9.8pt;line-height:1.42;color:#222}
      .tpl-elegant .t-header{text-align:center}
      .tpl-elegant .t-name{display:block;font-family:Georgia,"Times New Roman",serif;font-weight:400;font-size:28pt;margin:0;color:#111;letter-spacing:0}
      .tpl-elegant .t-title{font-size:12pt;letter-spacing:2px;text-transform:uppercase;margin-top:2px;color:#222}
      .tpl-elegant .t-rule{height:2px;background:#2a8a74;margin:12px 6% 10px}
      .tpl-elegant .t-end{margin-top:18px}
      .tpl-elegant .t-sum-h{font-size:11pt;letter-spacing:1px;text-transform:uppercase;margin:6px 0 4px;color:#111}
      .tpl-elegant .t-sum{font-style:italic;margin:0 6%;font-size:9.5pt}
      .tpl-elegant .t-contact{display:flex;justify-content:space-between;text-align:left;margin:12px 6% 0;font-size:9pt;gap:12px}
      .tpl-elegant .t-contact b{color:#2a8a74}
      .tpl-elegant .t-links{font-size:9pt;margin-top:6px;color:#333}
      .tpl-elegant .t-sec{margin:14px 6% 0}
      .tpl-elegant .t-sec h2{font-size:12pt;font-weight:700;color:#2a8a74;text-transform:uppercase;letter-spacing:.8px;margin:0 0 6px}
      .tpl-elegant .t-org{font-style:italic;color:#2a8a74}`,
  },

  modern: {
    name: "Modern",
    desc: "Grey section bands, skills grid",
    swatch: "#6b6f78",
    render: (r) => header(r) + sections(r, ["summary", "skills", "experience", "projects", "education", "certifications", "achievements"], "modern", (x) => S.skillsGrid(x, 3)),
    css: `
      .tpl-modern{font-family:"Helvetica Neue",Arial,sans-serif;font-size:9.8pt;line-height:1.42;color:#2b2b2b}
      .tpl-modern .t-name{font-size:22pt;font-weight:700;color:#3a3d44;margin:0;text-transform:uppercase;letter-spacing:.5px}
      .tpl-modern .t-title{font-size:12pt;font-weight:700;color:#2b2b2b;text-transform:uppercase;margin-top:4px}
      .tpl-modern .t-contact{font-size:8.8pt;color:#444;margin-top:4px}
      .tpl-modern .t-sec{margin-top:12px}
      .tpl-modern .t-sec h2{background:#dcdde0;color:#3a3d44;font-size:9.8pt;font-weight:700;font-style:italic;text-transform:uppercase;letter-spacing:.8px;padding:4px 14px;border-radius:12px;margin:0 0 6px}
      .tpl-modern .t-p{margin:0;text-align:justify}`,
  },

  minimal: {
    name: "Minimal",
    desc: "Bold black, ruled headings",
    swatch: "#111111",
    render: (r) => header(r) + sections(r, ["summary", "experience", "projects", "skills", "education", "certifications", "achievements"], "minimal", (x) => S.skillsGrid(x, 3)),
    css: `
      .tpl-minimal{font-family:Arial,"Helvetica Neue",sans-serif;font-size:9.8pt;line-height:1.4;color:#111}
      .tpl-minimal .t-name{font-size:24pt;font-weight:800;margin:0;text-transform:uppercase;letter-spacing:.3px}
      .tpl-minimal .t-title{font-size:12pt;font-weight:700;text-transform:uppercase;margin-top:2px}
      .tpl-minimal .t-contact{font-size:8.8pt;color:#333;margin-top:3px;padding-bottom:6px;border-bottom:1.5px solid #111}
      .tpl-minimal .t-sec{margin-top:12px}
      .tpl-minimal .t-sec h2{font-size:10.5pt;font-weight:800;text-transform:uppercase;border-bottom:1px solid #111;padding-bottom:2px;margin:0 0 6px}
      .tpl-minimal .t-p{margin:0;text-align:justify}`,
  },
};

// Base rules shared by every template (scoped to .tpl)
const TPL_BASE_CSS = `
  .tpl h1,.tpl h2{letter-spacing:normal;color:#111}
  .tpl ul{margin:3px 0 0;padding-left:18px}
  .tpl li{margin:1px 0}
  .tpl .t-item{margin-bottom:8px}
  .tpl .t-item:last-child{margin-bottom:0}
  .tpl .t-row{display:flex;justify-content:space-between;gap:12px}
  .tpl .t-date{white-space:nowrap;font-weight:700}
  .tpl .t-loc{font-style:italic;color:#444;font-weight:400}
  .tpl .t-grid{list-style:disc;display:grid;column-gap:18px;padding-left:18px;margin:0}
  .tpl .t-cols-2{grid-template-columns:1fr 1fr}
  .tpl .t-cols-3{grid-template-columns:1fr 1fr 1fr}
  .tpl .t-skill-line{margin:1px 0}`;

// Sample content so people can preview templates before generating
const SAMPLE_RESUME = {
  name: "Ananya Rao",
  title: "Data Analyst",
  contact: { email: "ananya.rao@email.com", phone: "+91 98765 43210", location: "Bengaluru, India", linkedin: "linkedin.com/in/ananyarao", github: "github.com/ananyarao", portfolio: "" },
  summary: "Data Analyst with 2+ years of experience turning raw business data into clear dashboards and decisions. Skilled in SQL, Python and Power BI, with a track record of cutting reporting time and surfacing revenue opportunities for sales and operations teams.",
  skills: [
    { category: "Analytics", items: ["SQL", "Python (Pandas)", "Excel", "Statistics"] },
    { category: "BI & Tools", items: ["Power BI", "Tableau", "Google Analytics", "Git"] },
    { category: "Data", items: ["PostgreSQL", "BigQuery", "ETL", "A/B Testing"] },
  ],
  experience: [
    { role: "Data Analyst", company: "Finlytics Pvt Ltd", location: "Bengaluru", start: "Jun 2024", end: "Present", bullets: ["Built 12 Power BI dashboards used by 40+ managers, cutting weekly reporting time by 60%.", "Automated SQL data pipelines for sales data, reducing manual errors by 35%.", "Ran A/B test analysis that lifted email conversion by 9%."] },
    { role: "Analytics Intern", company: "RetailCo", location: "Pune", start: "Jan 2024", end: "May 2024", bullets: ["Cleaned and modelled 1M+ transaction records in Python to analyse customer churn.", "Presented churn insights to leadership, informing a retention campaign."] },
  ],
  projects: [
    { name: "Customer Churn Predictor", tech: "Python, scikit-learn", bullets: ["Built a churn model with 86% accuracy and a Streamlit app to explore at-risk customers."] },
  ],
  education: [{ degree: "B.Tech, Computer Science", institution: "PES University", year: "2020 - 2024", details: "CGPA: 8.6 / 10" }],
  certifications: ["Google Data Analytics Professional Certificate", "Microsoft PL-300: Power BI Data Analyst"],
  achievements: [],
  ats: { score: 88, matchedKeywords: ["SQL", "Python", "Power BI", "Dashboards", "A/B Testing"], missingKeywords: [], tips: ["This is a sample. Generate your own resume to see your score and tips."] },
};

window.ResumeTemplates = { TEMPLATES, TPL_BASE_CSS, SAMPLE_RESUME };
})();
