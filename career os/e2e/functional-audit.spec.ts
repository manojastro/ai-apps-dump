import { test, expect, type Page } from "@playwright/test";
import type { AppData } from "../src/lib/domain/types";

// Audit fixtures live only in a fresh Playwright browser's local demo storage.
// These tests never authenticate to or write to a hosted workspace.
const KEY = "career-os-demo-v4";
async function state(page: Page): Promise<AppData> {
  return page.evaluate((key) => JSON.parse(localStorage.getItem(key)!), KEY);
}
async function clean(page: Page) {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Your career, in motion" })).toBeVisible();
  await page.evaluate((key) => {
    const value = JSON.parse(localStorage.getItem(key)!);
    localStorage.setItem(key, JSON.stringify(Object.fromEntries(Object.keys(value).map(k => [k, []]))));
  }, KEY);
  await page.reload();
  await expect(page.getByRole("heading", { name: "Your career, in motion" })).toBeVisible();
}
async function createTask(page: Page, title: string, links?: { goal?: string; project?: string; skill?: string }) {
  await page.goto("/tasks");
  await page.getByRole("button", { name: "New task", exact: true }).click();
  await page.getByLabel("Task", { exact: true }).fill(title);
  await page.getByLabel("Priority", { exact: true }).selectOption("high");
  if (links?.goal) await page.getByLabel("Goal", { exact: true }).selectOption({ label: links.goal });
  if (links?.project) await page.getByLabel("Project", { exact: true }).selectOption({ label: links.project });
  if (links?.skill) await page.getByLabel("Skill", { exact: true }).selectOption({ label: links.skill });
  await page.getByRole("button", { name: "Create task" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
}
async function summary(page: Page, label: string) {
  return page.locator(".summary-item").filter({ has: page.locator("span", { hasText: new RegExp(`^${label}$`) }) }).locator("strong");
}
test.beforeEach(async ({ page }) => { await clean(page); });

test("A: linked planning, timer pause/resume, completion, dashboard and log persist", async ({ page }) => {
  await createTask(page, "AUDIT A execution");
  await page.goto("/planner");
  await page.getByRole("button", { name: "Time block", exact: true }).click();
  await page.getByLabel("Task (optional)").selectOption({ label: "AUDIT A execution" });
  await page.getByRole("button", { name: "Save block" }).click();
  await page.goto("/today");
  await expect(page.getByRole("checkbox", { name: "Complete AUDIT A execution" })).toBeVisible();
  await page.clock.install();
  await page.getByRole("button", { name: "Focus", exact: true }).click();
  await page.clock.runFor(61_000);
  await page.getByRole("button", { name: "Pause", exact: true }).click();
  const paused = await page.getByRole("dialog").innerText();
  await page.clock.runFor(10_000);
  expect(await page.getByRole("dialog").innerText()).toBe(paused);
  await page.getByRole("button", { name: "Resume", exact: true }).click();
  await page.getByRole("button", { name: "Stop & save" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  let data = await state(page);
  expect(data.tasks[0].status).toBe("today");
  expect(data.tasks[0].actual_minutes).toBe(1);
  expect(data.focus_sessions).toHaveLength(1);
  await page.getByRole("checkbox", { name: "Complete AUDIT A execution" }).click();
  await expect(page.getByRole("checkbox", { name: "Complete AUDIT A execution" })).toHaveCount(0);
  await page.goto("/");
  await expect(await summary(page, "Completed this week")).toHaveText("1");
  await expect(await summary(page, "Actual this week")).toHaveText("1m");
  await page.goto("/daily-log");
  await expect(await summary(page, "Completed tasks")).toHaveText("1");
  await expect(await summary(page, "Focused work")).toHaveText("1m");
  await page.reload();
  data = await state(page);
  expect(data.tasks[0].status).toBe("completed");
  expect(data.tasks[0].actual_minutes).toBe(1);
  expect(data.focus_sessions).toHaveLength(1);
});

test("B: two milestones and a linked task update goal progress without unrelated tasks", async ({ page }) => {
  await page.goto("/goals");
  await page.getByRole("button", { name: "New goal" }).click();
  await page.getByLabel("Goal title").fill("AUDIT B goal");
  await page.getByLabel("Type", { exact: true }).selectOption("career");
  await page.getByRole("button", { name: "Create goal" }).click();
  for (const name of ["AUDIT checkpoint one", "AUDIT checkpoint two"]) {
    await page.getByRole("button", { name: "Add milestone" }).click();
    await page.getByLabel("Milestone title").fill(name);
    await page.getByRole("button", { name: "Create milestone" }).click();
  }
  await page.getByRole("button", { name: "Complete", exact: true }).first().click();
  await expect(page.getByRole("button", { name: /AUDIT B goal/ })).toContainText("50%");
  await page.getByRole("button", { name: "Complete", exact: true }).click();
  await expect(page.getByRole("button", { name: /AUDIT B goal/ })).toContainText("100%");
  await createTask(page, "AUDIT B linked", { goal: "AUDIT B goal" });
  await createTask(page, "AUDIT unrelated");
  await page.getByRole("checkbox", { name: "Complete AUDIT unrelated" }).click();
  await page.goto("/goals");
  await expect(page.getByRole("button", { name: /AUDIT B goal/ })).toContainText("67%");
  await page.goto("/tasks");
  await page.getByRole("checkbox", { name: "Complete AUDIT B linked" }).click();
  await page.goto("/goals");
  await expect(page.getByRole("button", { name: /AUDIT B goal/ })).toContainText("100%");
  expect((await state(page)).goals[0].status).toBe("active");
  await page.reload();
  await expect(page.getByRole("button", { name: /AUDIT B goal/ })).toContainText("100%");
  expect((await state(page)).milestones).toHaveLength(2);
});

test("C: manual skill topic, distinct readiness, linked task and evidence persist", async ({ page }) => {
  await page.goto("/skills");
  await page.getByRole("button", { name: "Add skill", exact: true }).click();
  await page.getByLabel("Skill name").fill("AUDIT C Skill");
  await page.getByRole("dialog").getByRole("button", { name: "Add skill", exact: true }).click();
  await page.getByRole("button", { name: "Add topic" }).click();
  await page.getByLabel("Topic name").fill("AUDIT manual topic");
  await page.getByRole("dialog").getByRole("button", { name: "Add topic" }).click();
  await page.getByLabel("Status for AUDIT manual topic").selectOption("Applied");
  await page.getByLabel("Knowledge level").selectOption("3");
  await page.getByLabel("Skill status", { exact: true }).selectOption("Practicing");
  await createTask(page, "AUDIT C practice", { skill: "AUDIT C Skill" });
  await page.getByRole("checkbox", { name: "Complete AUDIT C practice" }).click();
  await page.goto("/more");
  await page.getByRole("button", { name: "Evidence", exact: true }).click();
  await page.getByRole("button", { name: "Add proof" }).click();
  await page.getByLabel("Title", { exact: true }).fill("AUDIT C proof");
  await page.getByLabel("Skill", { exact: true }).selectOption({ label: "AUDIT C Skill" });
  await page.getByLabel("URL", { exact: true }).fill("https://example.com/audit-proof");
  await page.getByRole("button", { name: "Save evidence" }).click();
  await page.goto("/skills");
  await expect(page.getByText("AUDIT C proof")).toBeVisible();
  await page.reload();
  const data = await state(page);
  expect(data.skill_topics[0].status).toBe("Applied");
  expect(data.skills[0].knowledge).toBe(3);
  expect(data.skills[0].hands_on).toBe(0);
  expect(data.skills[0].interview).toBe(0);
  expect(data.evidence[0].skill_id).toBe(data.skills[0].id);
});

test("D: project links, status and completed task progress persist", async ({ page }) => {
  await page.goto("/projects");
  await page.getByRole("button", { name: "New project" }).click();
  await page.getByLabel("Project name").fill("AUDIT D Project");
  await page.getByRole("button", { name: "Create project" }).click();
  await page.getByLabel("GitHub URL").fill("https://github.com/example/audit");
  await page.getByLabel("Demo URL").fill("https://example.com/audit");
  await page.getByLabel("Architecture summary").fill("AUDIT notes");
  await page.getByLabel("Project status").selectOption("Building");
  await createTask(page, "AUDIT D task", { project: "AUDIT D Project" });
  await page.getByRole("checkbox", { name: "Complete AUDIT D task" }).click();
  await page.goto("/projects");
  await expect(page.getByRole("button", { name: /AUDIT D Project/ })).toContainText("100%");
  await page.reload();
  const project = (await state(page)).projects[0];
  expect(project.status).toBe("Building");
  expect(project.github_url).toBe("https://github.com/example/audit");
  expect(project.deployment_url).toBe("https://example.com/audit");
});

test("E: due followup reaches dashboard and interaction history persists", async ({ page }) => {
  await page.goto("/networking");
  await page.getByRole("button", { name: "Add contact" }).click();
  await page.getByLabel("Name", { exact: true }).fill("AUDIT E Contact");
  await page.getByLabel("Next follow-up", { exact: true }).fill("2000-01-01");
  await page.getByLabel("LinkedIn URL").fill("https://www.linkedin.com/in/audit-example/");
  await page.getByRole("dialog").getByRole("button", { name: "Add contact" }).click();
  await page.goto("/");
  await expect(page.getByText("Follow up with AUDIT E Contact")).toBeVisible();
  await page.goto("/networking");
  await page.getByRole("button", { name: "Log interaction" }).click();
  await page.getByRole("dialog").getByLabel("Next follow-up").fill("2099-01-01");
  await page.getByRole("dialog").getByLabel("Notes", { exact: true }).fill("AUDIT E interaction");
  await page.getByRole("button", { name: "Save interaction" }).click();
  await page.reload();
  await expect(page.getByText("AUDIT E interaction")).toBeVisible();
  await page.goto("/");
  await expect(await summary(page, "Needs attention")).toHaveText("0");
});

test("F: interview answer and repeated practice update dashboard and log", async ({ page }) => {
  await page.goto("/interviews");
  await page.getByRole("button", { name: "Add question" }).click();
  await page.getByLabel("Question", { exact: true }).fill("AUDIT F Explain SQL indexes");
  await page.getByRole("button", { name: "Save question" }).click();
  await page.getByLabel("Working answer").fill("AUDIT indexing answer");
  for (const level of ["2", "4"]) {
    await page.getByRole("button", { name: "Record practice" }).click();
    await page.getByLabel("Confidence (0–4)").selectOption(level);
    await page.getByRole("button", { name: "Save practice" }).click();
  }
  await page.reload();
  const data = await state(page);
  expect(data.interview_practice).toHaveLength(2);
  expect(data.interview_questions[0].practice_count).toBe(2);
  expect(data.interview_questions[0].answer).toBe("AUDIT indexing answer");
  await page.goto("/");
  await expect(page.locator("section").filter({ has: page.getByRole("heading", { name: "Interview prep", exact: true }) })).toContainText("1 / 1");
  await page.goto("/daily-log");
  await expect(await summary(page, "Questions practiced")).toHaveText("2");
});

test("G: every supported job stage changes one record and notes persist", async ({ page }) => {
  await page.goto("/jobs");
  await page.getByRole("button", { name: "Add application" }).click();
  await page.getByLabel("Company", { exact: true }).fill("AUDIT G Company");
  await page.getByLabel("Role", { exact: true }).fill("AUDIT Engineer");
  await page.getByRole("button", { name: "Save application" }).click();
  for (const stage of ["Saved", "Applied", "Recruiter Contact", "Screening", "Technical Interview", "Hiring Manager", "Final Round", "Offer", "Rejected", "Withdrawn"]) {
    await page.getByLabel("Stage for AUDIT G Company").selectOption(stage);
    expect((await state(page)).job_applications).toHaveLength(1);
  }
  await page.getByRole("button", { name: "Kanban", exact: true }).click();
  await page.getByLabel("Move AUDIT G Company").selectOption("Applied");
  await page.getByLabel("Application notes").fill("AUDIT G notes");
  await page.getByLabel("Job description", { exact: true }).fill("AUDIT G role requires Python and Docker");
  await page.getByRole("heading", { name: "Job applications", exact: true }).click();
  await page.reload();
  await expect(page.getByLabel("Application notes")).toHaveValue("AUDIT G notes");
  const data = await state(page);
  expect(data.job_applications).toHaveLength(1);
  expect(data.job_applications[0].status).toBe("Applied");
  await page.goto("/");
  await expect(page.locator("section").filter({ has: page.getByRole("heading", { name: "Applications", exact: true }) })).toContainText("1");
});

test("H: local Copilot writes require explicit confirmation and avoid repeat confirmation", async ({ page }) => {
  await page.goto("/copilot");
  await page.getByLabel("Copilot command").fill("Create AUDIT H FastAPI");
  await page.getByRole("button", { name: "Run command" }).click();
  await expect(page.getByText("Create task: AUDIT H FastAPI")).toBeVisible();
  expect((await state(page)).tasks).toHaveLength(0);
  await page.getByRole("button", { name: "Confirm 1 change" }).click();
  await expect(page.getByRole("button", { name: "All saved" })).toBeDisabled();
  expect((await state(page)).tasks).toHaveLength(1);
  await page.reload();
  expect((await state(page)).tasks).toHaveLength(1);
});

test("I: notes, resources, inbox conversion, journal and JSON export preserve data", async ({ page }) => {
  await page.goto("/more");
  await page.getByRole("button", { name: "Notes", exact: true }).click();
  await page.getByRole("button", { name: "New note" }).click();
  await page.getByLabel("Title", { exact: true }).fill("AUDIT I note");
  await page.locator(".rich-editor").fill("AUDIT I persistent content");
  await expect(page.getByRole("status")).toHaveText("Saved");
  await page.getByRole("button", { name: "Resources", exact: true }).click();
  await page.getByRole("button", { name: "Save resource", exact: true }).click();
  await page.getByLabel("Title", { exact: true }).fill("AUDIT I resource");
  await page.getByLabel("URL", { exact: true }).fill("https://example.com/audit-resource");
  await page.getByRole("dialog").getByRole("button", { name: "Save resource" }).click();
  await page.getByRole("button", { name: "Inbox", exact: true }).click();
  await page.getByLabel("Inbox capture").fill("Learn AUDIT I inbox item");
  await page.getByRole("button", { name: "Add", exact: true }).click();
  await page.getByRole("button", { name: "Classify & save" }).click();
  await page.getByRole("button", { name: "Export", exact: true }).click();
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download JSON backup" }).click();
  const download = await downloadPromise;
  const stream = await download.createReadStream();
  const chunks: Buffer[] = [];
  for await (const chunk of stream!) chunks.push(Buffer.from(chunk));
  const exported = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  expect(exported.source).toBe("demo");
  expect(exported.data.notes[0].content).toContain("AUDIT I persistent content");
  expect(exported.data.resources).toHaveLength(1);
  expect(exported.data.tasks).toHaveLength(1);
  await page.goto("/daily-log");
  await page.getByLabel("Journal notes").fill("AUDIT I journal");
  await page.getByRole("button", { name: "Save journal" }).click();
  await expect(page.getByRole("status")).toHaveText("Journal saved.");
  await page.reload();
  await expect(page.getByLabel("Journal notes")).toHaveValue("AUDIT I journal");
  const reloaded = await state(page);
  expect(reloaded.notes[0].content).toContain("AUDIT I persistent content");
  expect(reloaded.resources[0].url).toBe("https://example.com/audit-resource");
  await page.getByLabel("Log date").fill("2000-01-01");
  await expect(await summary(page, "Completed tasks")).toHaveText("0");
  await expect(page.getByLabel("Journal notes")).toHaveValue("");
});

test("desktop/tablet/mobile navigation, dark mode, shortcuts and layouts", async ({ page }) => {
  const overflows: string[] = [];
  for (const width of [1440, 768, 390]) {
    await page.setViewportSize({ width, height: 900 });
    for (const route of ["/", "/today", "/planner", "/tasks", "/goals", "/skills", "/projects", "/networking", "/interviews", "/jobs", "/daily-log", "/copilot", "/more", "/settings"]) {
      await page.goto(route);
      await expect(page.locator("main h1")).toBeVisible();
      const actual = await page.evaluate(() => document.documentElement.scrollWidth);
      if (actual > width) overflows.push(`${route} at ${width}: ${actual}px`);
    }
  }
  await page.getByRole("button", { name: "Switch to dark mode" }).click();
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.keyboard.press("c");
  await expect(page.getByRole("dialog", { name: "Quick capture" })).toBeVisible();
  await page.keyboard.press("Escape");
  await page.keyboard.press("t");
  await expect(page.getByRole("dialog", { name: "New task" })).toBeVisible();
  await page.keyboard.press("Escape");
  await page.keyboard.press("/");
  await expect(page.getByRole("dialog", { name: "Search Career OS" })).toBeVisible();
  expect(overflows).toEqual([]);
});

// Reproductions assert the expected user behavior. Failures are audit findings,
// not reasons to change production code during this audit.
test("DEFECT: arbitrary start time should remain visible in Planner day view", async ({ page }) => {
  await page.goto("/planner");
  await page.getByRole("button", { name: "Time block", exact: true }).click();
  await page.getByLabel("Title", { exact: true }).fill("AUDIT hidden 08:30 block");
  await page.getByLabel("Start", { exact: true }).fill("08:30");
  await page.getByLabel("End", { exact: true }).fill("09:15");
  await page.getByRole("button", { name: "Save block" }).click();
  expect((await state(page)).planner_blocks).toHaveLength(1);
  await page.getByRole("button", { name: "Today", exact: true }).click();
  await expect(page.getByText("AUDIT hidden 08:30 block", { exact: true })).toBeVisible({ timeout: 1500 });
});

test("DEFECT: choosing Completed in task editor should populate completion date", async ({ page }) => {
  await createTask(page, "AUDIT editor completed");
  await page.getByRole("button", { name: "Edit AUDIT editor completed" }).click();
  await page.getByLabel("Stage", { exact: true }).selectOption("completed");
  await page.getByRole("button", { name: "Save task" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  expect((await state(page)).tasks[0].completed_at).not.toBeNull();
});

test("DEFECT: completing a focused task should retain Today actual total", async ({ page }) => {
  await createTask(page, "AUDIT Today actual");
  await page.getByRole("button", { name: "Edit AUDIT Today actual" }).click();
  await page.getByLabel("Stage", { exact: true }).selectOption("today");
  await page.getByRole("button", { name: "Save task" }).click();
  await page.goto("/today");
  await page.getByRole("button", { name: "Focus", exact: true }).click();
  await page.getByRole("button", { name: "Stop & save" }).click();
  await expect(await summary(page, "Actual")).toHaveText("1m");
  await page.getByRole("checkbox", { name: "Complete AUDIT Today actual" }).click();
  await expect(await summary(page, "Actual")).toHaveText("1m", { timeout: 1500 });
});

test("DEFECT: focus session should survive a page refresh", async ({ page }) => {
  await createTask(page, "AUDIT interrupted focus");
  await page.getByRole("button", { name: "Focus", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Focus session" })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("dialog", { name: "Focus session" })).toBeVisible({ timeout: 1500 });
});

test("DEFECT: manual duplicate skill should be rejected consistently with hosted mode", async ({ page }) => {
  for (let i = 0; i < 2; i++) {
    await page.goto("/skills");
    await page.getByRole("button", { name: "Add skill", exact: true }).click();
    await page.getByLabel("Skill name").fill("AUDIT duplicate");
    await page.getByRole("dialog").getByRole("button", { name: "Add skill", exact: true }).click();
    await expect(page.getByRole("dialog")).toHaveCount(0);
  }
  expect((await state(page)).skills).toHaveLength(1);
});

test("DEFECT: modal dialog should keep keyboard focus inside", async ({ page }) => {
  await page.keyboard.press("c");
  const dialog = page.getByRole("dialog", { name: "Quick capture" });
  await expect(dialog).toBeVisible();
  await dialog.getByRole("button", { name: "Close", exact: true }).focus();
  await page.keyboard.press("Shift+Tab");
  expect(await dialog.evaluate(el => el.contains(document.activeElement))).toBe(true);
});

test("focus Complete task saves exactly one session and updates the daily log", async ({ page }) => {
  await createTask(page, "AUDIT focus complete");
  await page.clock.install();
  await page.getByRole("button", { name: "Focus", exact: true }).click();
  await page.clock.runFor(61_000);
  await page.getByRole("button", { name: "Complete task", exact: true }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.reload();
  const data = await state(page);
  expect(data.tasks[0].status).toBe("completed");
  expect(data.tasks[0].completed_at).not.toBeNull();
  expect(data.tasks[0].actual_minutes).toBe(1);
  expect(data.focus_sessions).toHaveLength(1);
  await page.goto("/daily-log");
  await expect(await summary(page, "Completed tasks")).toHaveText("1");
  await expect(await summary(page, "Focused work")).toHaveText("1m");
});

test("DEFECT: editing task schedule should move its linked Planner block", async ({ page }) => {
  await createTask(page, "AUDIT schedule consistency");
  await page.goto("/planner");
  await page.getByRole("button", { name: "Time block", exact: true }).click();
  await page.getByLabel("Task (optional)").selectOption({ label: "AUDIT schedule consistency" });
  await page.getByRole("button", { name: "Save block" }).click();
  await page.goto("/tasks");
  await page.getByRole("button", { name: "Edit AUDIT schedule consistency" }).click();
  await page.getByLabel("Scheduled day", { exact: true }).fill("2099-01-01");
  await page.getByRole("button", { name: "Save task" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.reload();
  const data = await state(page);
  expect(data.tasks[0].scheduled_date).toBe("2099-01-01");
  expect(data.planner_blocks[0].block_date).toBe(data.tasks[0].scheduled_date);
});

test("DEFECT: Copilot should preserve requested high priority", async ({ page }) => {
  await page.goto("/copilot");
  await page.getByLabel("Copilot command").fill("Create a high-priority task to review FastAPI");
  await page.getByRole("button", { name: "Run command" }).click();
  await page.getByRole("button", { name: "Confirm 1 change" }).click();
  await expect(page.getByRole("button", { name: "All saved" })).toBeDisabled();
  await page.reload();
  expect((await state(page)).tasks[0].priority).toBe("high");
});
