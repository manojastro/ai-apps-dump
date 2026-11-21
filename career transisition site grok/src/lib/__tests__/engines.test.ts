import { describe, expect, it } from "vitest";
import { createDemoState } from "@/data/demo-data";
import { createEmptyState } from "@/lib/empty-state";
import { skillEvidenceConfidence } from "@/lib/evidence";
import { findDuplicateJobs } from "@/lib/duplicates";
import { funnelMetrics, smallSample } from "@/lib/analytics";
import { isOverdue, weekStartIso, addDaysIso, isoDate, todayInTz } from "@/lib/dates";
import { migrateState, needsMigration } from "@/lib/migrations";
import { opportunityFit } from "@/lib/opportunity-fit";
import { rankActions } from "@/lib/priority-engine";
import { detectRisks, currentBottleneck } from "@/lib/risks";
import { analyzeRole } from "@/lib/role-readiness";
import {
  applicationQualityValue,
  captureSnapshot,
  computeReadiness,
  projectProductionScore,
} from "@/lib/scoring";
import { parseCareerState } from "@/lib/validation";
import { parseImportedState, previewImport } from "@/lib/export-import";
import { LocalStorageRepository } from "@/lib/storage";
import { newJob, newProject, newSkill } from "@/lib/factories";
import { timestamps } from "@/lib/ids";
import type { CareerOSState, JobApplication } from "@/types/career";

function deep(state: CareerOSState): CareerOSState {
  return JSON.parse(JSON.stringify(state)) as CareerOSState;
}

describe("readiness scoring", () => {
  it("scores an empty workspace low and does not fabricate history", () => {
    const empty = createEmptyState();
    const r = computeReadiness(empty);
    expect(r.global).toBeLessThan(35);
    expect(r.evidence).toBe(0);
    expect(empty.scoreSnapshots).toHaveLength(0);
  });

  it("does not let fifty identified applications imply career readiness", () => {
    const state = createEmptyState();
    state.applications = Array.from({ length: 50 }, (_, i) =>
      newJob({
        id: `j${i}`,
        company: `Co ${i}`,
        role: "Agentic AI Engineer",
        status: "Identified",
        dateApplied: "2026-01-01",
        nextFollowUpDate: "",
      }),
    );
    const r = computeReadiness(state);
    expect(r.marketExecution).toBeLessThan(40);
    expect(r.global).toBeLessThan(40);
  });

  it("weights quality over planned-project count", () => {
    const planned = createEmptyState();
    planned.projects = Array.from({ length: 10 }, (_, i) =>
      newProject({
        id: `p${i}`,
        title: `Outline ${i}`,
        status: "planned",
        maturity: "Tutorial",
      }),
    );
    const strong = createEmptyState();
    strong.projects = [
      newProject({
        id: "prod",
        title: "Eval CI",
        status: "deployed",
        maturity: "Production Grade",
        category: "Agents",
        useCase: "Treat agent graphs like software with golden tasks, trajectory scores, cost budgets, and regression gates on every pull request.",
        architectureSummary: "Eval runner as CI. Stores traces, scores, diffs. Blocks merge on quality or cost SLO breach with isolated tenants.",
        evaluationNotes: "80 tasks, nightly plus PR, mixed human labels and deterministic checks for trajectory success.",
        testingNotes: "Runner unit tests and flake quarantine policy documented with fixtures.",
        safetyNotes: "No production credentials in CI. Tenant isolation and secret scanning on traces.",
        observabilityNotes: "Dashboards for pass rate, cost, latency, flake, and model version.",
        failureHandlingNotes: "Quarantine flaky tasks rather than hiding regressions. Retry with backoff.",
        documentationNotes: "Protocol and contribution guide live in the repository.",
        githubUrl: "https://github.com/example/eval-ci",
        liveUrl: "https://eval.example.com",
        techStack: ["Python", "pytest", "Docker", "GitHub Actions", "LangGraph"],
      }),
    ];
    strong.projectMetrics = [
      { id: "m1", ...timestamps(), projectId: "prod", name: "Catch rate", achieved: "3", methodology: "fixtures", notes: "" },
      { id: "m2", ...timestamps(), projectId: "prod", name: "Pass", achieved: "0.9", methodology: "golden", notes: "" },
    ];
    const plannedScore = computeReadiness(planned).evidence;
    const strongScore = computeReadiness(strong).evidence;
    expect(strongScore).toBeGreaterThan(plannedScore);
    expect(projectProductionScore(strong, strong.projects[0]!).total).toBeGreaterThan(55);
  });
});

describe("skill evidence", () => {
  it("does not give a mastered skill full evidence confidence without artifacts", () => {
    const state = createEmptyState();
    const skill = newSkill({
      id: "sk1",
      name: "LangGraph",
      status: "mastered",
      summary: "",
      sourceLearned: "",
      mappedRoles: [],
    });
    state.skills = [skill];
    const conf = skillEvidenceConfidence(state, skill);
    expect(conf).toBeLessThan(0.55);
    expect(conf).toBeGreaterThanOrEqual(0.4);
  });

  it("raises confidence when project and artifact evidence exist", () => {
    const state = createEmptyState();
    const skill = newSkill({
      id: "sk1",
      name: "LangGraph",
      status: "mastered",
      summary: "Stateful graphs",
      sourceLearned: "RCA platform",
      mappedRoles: ["Agentic AI Engineer"],
    });
    state.skills = [skill];
    state.projects = [newProject({ id: "p1", title: "RCA", status: "deployed", techStack: ["LangGraph"] })];
    state.evidenceArtifacts = [
      {
        id: "e1",
        ...timestamps(),
        title: "Eval",
        type: "Evaluation Report",
        description: "report",
        skillIds: ["sk1"],
        competencyIds: [],
        mappedRoleIds: [],
        strength: "Strong",
      },
    ];
    expect(skillEvidenceConfidence(state, skill)).toBeGreaterThan(0.7);
  });
});

describe("role readiness", () => {
  it("uses competency requirements rather than title matching alone", () => {
    const demo = createDemoState();
    const agentic = demo.targetRoles.find((r) => r.id === "role_agentic")!;
    const result = analyzeRole(demo, agentic);
    expect(result.score).toBeGreaterThan(0);
    expect(result.gaps.length).toBe(agentic.competencyRequirements.length);
    expect(result.strong.length + result.partial.length + result.missing.length + result.evidenceMissing.length).toBe(result.gaps.length);
  });
});

describe("opportunity fit and application quality", () => {
  it("labels a well-aligned referred role as Strong Apply or Apply", () => {
    const demo = createDemoState();
    const job = demo.applications.find((a) => a.id === "demo_job_1")!;
    const fit = opportunityFit(demo, job);
    expect(["Strong Apply", "Apply"]).toContain(fit.label);
    expect(applicationQualityValue(job, demo)).toBeGreaterThan(50);
  });

  it("surfaces constraint conflict without auto-rejecting", () => {
    const state = createEmptyState();
    const job = newJob({
      company: "Faraway",
      role: "Agentic AI Engineer",
      location: "Reykjavik",
      compensationText: "4 LPA",
      interest: 2,
    });
    const fit = opportunityFit(state, job);
    expect(fit.constraints.length).toBeGreaterThan(0);
    expect(fit.label === "Constraint Conflict" || fit.constraints.length >= 1).toBe(true);
  });
});

describe("funnel and small samples", () => {
  it("warns when conversion denominators are small", () => {
    expect(smallSample(3)).toBe(true);
    expect(smallSample(8)).toBe(false);
    const apps: JobApplication[] = [
      newJob({ status: "Applied" }),
      newJob({ status: "Screening" }),
    ];
    const funnel = funnelMetrics(apps);
    expect(funnel.appliedToScreening.warning).toBe("Insufficient Data");
    expect(funnel.counts.Applied).toBe(1);
  });
});

describe("priority and risk engines", () => {
  it("ranks overdue follow-ups and evidence gaps", () => {
    const demo = createDemoState();
    demo.applications[0]!.nextFollowUpDate = "2020-01-01";
    demo.applications[0]!.status = "Applied";
    const actions = rankActions(demo);
    expect(actions.length).toBeGreaterThan(0);
    expect(actions.length).toBeLessThanOrEqual(5);
    const risks = detectRisks(demo);
    expect(Array.isArray(risks)).toBe(true);
    const bottleneck = currentBottleneck(demo);
    expect(bottleneck.kind).toBeTruthy();
  });
});

describe("dates", () => {
  it("treats past dates as overdue and formats week starts", () => {
    expect(isOverdue("2000-01-01")).toBe(true);
    expect(weekStartIso().length).toBe(10);
    const today = isoDate(todayInTz());
    expect(addDaysIso(today, 1) > today).toBe(true);
  });
});

describe("duplicate detection", () => {
  it("matches normalized company + role + url", () => {
    const existing = [newJob({ id: "a", company: "Contoso GCC", role: "Agentic AI Engineer", jobUrl: "https://careers.example.com/agentic/" })];
    const dupes = findDuplicateJobs(
      { id: "b", company: "contoso   gcc", role: "Agentic AI Engineer", jobUrl: "https://careers.example.com/agentic" },
      existing,
    );
    expect(dupes).toHaveLength(1);
  });
});

describe("storage migration and import validation", () => {
  it("migrates an old payload and validates with Zod", () => {
    expect(needsMigration({ version: 0, skills: [] })).toBe(true);
    const migrated = migrateState({
      version: 0,
      skills: [{ id: "s1", createdAt: "t", updatedAt: "t", name: "Python", category: "core_python", sourceLearned: "", sourceUrl: "", summary: "", whatNext: "", mappedRoles: [], status: "to_learn" }],
      projects: [{ id: "p1", createdAt: "t", updatedAt: "t", title: "RCA", category: "AIOps", targetRole: "AIOps Engineer", techStack: [], useCase: "", architectureSummary: "", githubUrl: "", liveUrl: "", starPitch: "", status: "planned" }],
    });
    const parsed = parseCareerState(migrated);
    expect(parsed.success).toBe(true);
    if (parsed.success) {
      expect(parsed.data.version).toBe(1);
      expect(parsed.data.projects[0]?.maturity).toBe("Prototype");
      expect(parsed.data.ui).toBeTruthy();
    }
  });

  it("rejects invalid import JSON and accepts a wrapped bundle", () => {
    const current = createEmptyState();
    const bad = previewImport("{not json", current);
    expect(bad.valid).toBe(false);
    const demo = createDemoState();
    const raw = JSON.stringify({ schemaVersion: 1, exportedAt: "2026-09-01", state: demo });
    const good = previewImport(raw, current);
    expect(good.valid).toBe(true);
    const imported = parseImportedState(raw);
    expect(imported.skills.length).toBeGreaterThan(0);
  });

  it("never treats corrupted storage as a successful load", async () => {
    localStorage.clear();
    localStorage.setItem("ai_career_os_state_v1", "{bad");
    const repo = new LocalStorageRepository();
    const result = await repo.load();
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.recovery.reason.length).toBeGreaterThan(0);
  });

  it("saves last-known-good after a valid persist", async () => {
    localStorage.clear();
    const repo = new LocalStorageRepository();
    const state = createEmptyState();
    await repo.save(state);
    const lkg = localStorage.getItem("ai_career_os_state_v1_lkg");
    expect(lkg).toBeTruthy();
  });
});

describe("snapshots", () => {
  it("captures derived scores without making them authoritative state", () => {
    const demo = createDemoState();
    const snap = captureSnapshot(demo, { role_agentic: 50 });
    expect(snap.globalReadiness).toBe(computeReadiness(demo).global);
    expect(demo.scoreSnapshots.find((s) => s.id === snap.id)).toBeUndefined();
  });
});

describe("demo workspace", () => {
  it("is labeled demo and parses as valid state", () => {
    const demo = createDemoState();
    expect(demo.ui.demoMode).toBe(true);
    expect(parseCareerState(deep(demo)).success).toBe(true);
    expect(demo.projects.some((p) => p.title.includes("RCA"))).toBe(true);
  });
});
