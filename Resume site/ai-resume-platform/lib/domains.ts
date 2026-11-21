export interface JobDomain {
  id: string;
  name: string;
  icon: string;
  keywords: string[];
}

export const JOB_DOMAINS: JobDomain[] = [
  {
    id: "ai-ml",
    name: "AI/ML & Agentic AI",
    icon: "🤖",
    keywords: [
      "machine learning",
      "artificial intelligence",
      "deep learning",
      "nlp",
      "llm",
      "genai",
      "data scientist",
      "ml engineer",
    ],
  },
  {
    id: "fullstack",
    name: "Full-Stack Development",
    icon: "💻",
    keywords: [
      "full stack",
      "fullstack",
      "mern",
      "react",
      "node",
      "frontend",
      "backend",
      "web developer",
    ],
  },
  {
    id: "cloud-devops",
    name: "Cloud & DevOps",
    icon: "☁️",
    keywords: [
      "devops",
      "cloud",
      "aws",
      "azure",
      "kubernetes",
      "docker",
      "sre",
      "infrastructure",
    ],
  },
  {
    id: "data-engineering",
    name: "Data Engineering",
    icon: "📊",
    keywords: [
      "data engineer",
      "etl",
      "spark",
      "airflow",
      "data pipeline",
      "big data",
      "warehouse",
    ],
  },
  {
    id: "mobile",
    name: "Mobile Development",
    icon: "📱",
    keywords: [
      "android",
      "ios",
      "flutter",
      "react native",
      "mobile developer",
      "swift",
      "kotlin",
    ],
  },
  {
    id: "cybersecurity",
    name: "Cybersecurity",
    icon: "🔒",
    keywords: [
      "security",
      "cybersecurity",
      "penetration",
      "soc",
      "infosec",
      "vulnerability",
    ],
  },
  {
    id: "product-management",
    name: "Product Management",
    icon: "📋",
    keywords: [
      "product manager",
      "product owner",
      "apm",
      "product management",
      "roadmap",
    ],
  },
  {
    id: "fintech",
    name: "FinTech & Banking",
    icon: "🏦",
    keywords: [
      "fintech",
      "banking",
      "payments",
      "blockchain",
      "financial",
      "insurance tech",
    ],
  },
];

export function classifyByKeywords(title: string): string {
  const lower = title.toLowerCase();
  let bestMatch = JOB_DOMAINS[0].id;
  let bestScore = 0;

  for (const domain of JOB_DOMAINS) {
    let score = 0;
    for (const kw of domain.keywords) {
      if (lower.includes(kw)) score += kw.split(" ").length;
    }
    if (score > bestScore) {
      bestScore = score;
      bestMatch = domain.id;
    }
  }
  return bestMatch;
}