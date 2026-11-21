export const APP_NAME = "AI Career OS";
export const APP_TAGLINE = "₹11 LPA → ₹20–35+ LPA AI Engineering";
export const SCHEMA_VERSION = 1;
export const STORAGE_KEY = "ai_career_os_state_v1";
export const LKG_KEY = "ai_career_os_state_v1_lkg";
export const RECOVERY_KEY = "ai_career_os_state_v1_recovery";
export const SYNC_CHANNEL = "ai_career_os_sync_v1";
export const IDB_NAME = "ai_career_os_idb";
export const IDB_ATTACHMENTS = "attachments";
export const DEFAULT_LOCALE = "en-IN";
export const DEFAULT_TIMEZONE = "Asia/Kolkata";
export const DEFAULT_CURRENCY = "INR";

export const TARGET_ROLE_NAMES = [
  "Agentic AI Engineer",
  "GenAI Engineer",
  "AIOps Engineer",
  "AI Solutions Engineer",
  "AI Solutions Architect",
  "Cloud AI Engineer",
  "Forward Deployed / AI Deployment Engineer",
  "Intelligent Automation Engineer",
  "AI Security Engineer",
  "LLM Engineer",
] as const;

export const TARGET_LOCATIONS = [
  "Bengaluru",
  "Hyderabad",
  "Chennai",
  "Coimbatore",
  "Remote India",
  "Hybrid India",
] as const;

export const SKILL_CATEGORIES = [
  { value: "core_python", label: "Core Python" },
  { value: "intermediate_python", label: "Intermediate Python" },
  { value: "llm_orchestration", label: "LLM Orchestration" },
  { value: "agents", label: "Agents" },
  { value: "rag", label: "RAG" },
  { value: "serving_llmops", label: "Serving / LLMOps" },
] as const;

export const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: "LayoutDashboard" },
  { href: "/today", label: "Today", icon: "Sunrise" },
  { href: "/skills", label: "Skills", icon: "Brain" },
  { href: "/projects", label: "Projects", icon: "Layers" },
  { href: "/evidence", label: "Evidence", icon: "ShieldCheck" },
  { href: "/roles", label: "Roles", icon: "Target" },
  { href: "/jobs", label: "Jobs", icon: "Briefcase" },
  { href: "/companies", label: "Companies", icon: "Building2" },
  { href: "/network", label: "Network", icon: "Users" },
  { href: "/interview", label: "Interview", icon: "Mic" },
  { href: "/certifications", label: "Certifications", icon: "Award" },
  { href: "/research", label: "Research", icon: "FlaskConical" },
  { href: "/execution", label: "Execution", icon: "Kanban" },
  { href: "/analytics", label: "Analytics", icon: "ChartLine" },
  { href: "/assets", label: "Assets", icon: "FolderKanban" },
  { href: "/settings", label: "Settings", icon: "Settings" },
] as const;

export const SMALL_SAMPLE_THRESHOLD = 5;
