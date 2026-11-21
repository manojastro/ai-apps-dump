"use client";

import { useCallback, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ChatStepper } from "./ChatStepper";
import { useResumeStore } from "@/store/resumeStore";
import { useToastStore } from "@/store/toastStore";
import type { ResumeData } from "@/lib/resumeSchema";

const STEPS = [
  { key: "fullName", label: "What\u2019s your name?", type: "input" as const },
  { key: "email", label: "Email address", type: "input" as const },
  { key: "phone", label: "Phone number", type: "input" as const },
  { key: "location", label: "Where are you based?", type: "input" as const },
  { key: "targetRole", label: "What role are you going for?", type: "input" as const },
  { key: "summary", label: "Tell us about yourself", type: "textarea" as const },
  { key: "experience", label: "Your work experience", type: "textarea" as const },
  { key: "education", label: "Education background", type: "textarea" as const },
  { key: "skills", label: "Key skills", type: "textarea" as const },
  { key: "certifications", label: "Anything else? Certs, projects...", type: "textarea" as const },
];

function applyChatAnswer(resume: ResumeData, key: string, value: string): ResumeData {
  const updated = { ...resume, personalInfo: { ...resume.personalInfo } };
  switch (key) {
    case "fullName": updated.personalInfo.fullName = value; break;
    case "email": updated.personalInfo.email = value; break;
    case "phone": updated.personalInfo.phone = value; break;
    case "location": updated.personalInfo.location = value; break;
    case "targetRole": updated.targetRole = value; break;
    case "summary": updated.summary = value; break;
    case "experience":
      updated.experience = [{ company: "", role: "", location: "", startDate: "", endDate: "", current: false, bullets: value.split("\n").filter(Boolean) }];
      break;
    case "education":
      updated.education = [{ institution: value.split(",")[0]?.trim() || value, degree: value.split(",")[1]?.trim() || "", field: "", startDate: "", endDate: "" }];
      break;
    case "skills": {
      const items = value.split(",").map((s) => s.trim()).filter(Boolean);
      updated.skills = { technical: items, soft: [] };
      break;
    }
    case "certifications":
      if (value.trim()) updated.certifications = [{ name: value, issuer: "", date: "" }];
      break;
  }
  return updated;
}

export function GuidedChatTab() {
  const {
    chatStep, setChatStep, chatAnswers, setChatAnswer,
    resume, setResume, isEnhancing, setIsEnhancing, setEnhanceError,
    targetJobDescription, setMobilePane,
  } = useResumeStore();
  const addToast = useToastStore((s) => s.addToast);

  const currentStep = STEPS[chatStep];
  const isLastStep = chatStep >= STEPS.length - 1;
  const currentValue = chatAnswers[currentStep?.key] ?? "";

  const handleNext = useCallback(() => {
    if (!currentStep || !currentValue.trim()) return;
    setResume(applyChatAnswer(resume, currentStep.key, currentValue));
    if (!isLastStep) setChatStep(chatStep + 1);
  }, [currentStep, currentValue, resume, setResume, isLastStep, chatStep, setChatStep]);

  const handleEnhance = useCallback(async () => {
    setIsEnhancing(true);
    setEnhanceError(null);
    setMobilePane("preview");
    const rawText = STEPS.map((s) => `${s.label}\n${chatAnswers[s.key] || ""}`).join("\n\n");
    try {
      const res = await fetch("/api/resume/enhance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rawText, targetJobDescription: targetJobDescription || undefined, existingResumeJson: resume }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || "Enhancement failed");
      }
      setResume(await res.json(), true);
      addToast("Resume polished with AI", "success");
    } catch (e) {
      setEnhanceError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setIsEnhancing(false);
    }
  }, [chatAnswers, targetJobDescription, resume, setIsEnhancing, setEnhanceError, setResume, addToast, setMobilePane]);

  const canEnhance = useMemo(
    () => chatAnswers.fullName && (chatAnswers.experience || chatAnswers.education),
    [chatAnswers]
  );

  if (!currentStep) return null;

  return (
    <div className="space-y-8">
      <ChatStepper total={STEPS.length} current={chatStep} />

      <div>
        <p className="text-[21px] font-medium text-[#1d1d1f] tracking-tight leading-snug">
          {currentStep.label}
        </p>
      </div>

      {currentStep.type === "textarea" ? (
        <Textarea
          id="chat-input"
          aria-label={currentStep.label}
          className="min-h-[140px]"
          value={currentValue}
          onChange={(e) => setChatAnswer(currentStep.key, e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && e.ctrlKey) handleNext(); }}
        />
      ) : (
        <Input
          id="chat-input"
          aria-label={currentStep.label}
          value={currentValue}
          onChange={(e) => setChatAnswer(currentStep.key, e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") handleNext(); }}
        />
      )}

      <div className="flex items-center gap-6">
        {chatStep > 0 && (
          <Button variant="ghost" onClick={() => setChatStep(chatStep - 1)}>
            Back
          </Button>
        )}
        {!isLastStep ? (
          <Button onClick={handleNext} disabled={!currentValue.trim()}>
            Continue
          </Button>
        ) : (
          <Button onClick={handleEnhance} disabled={!canEnhance || isEnhancing} size="lg">
            {isEnhancing ? "Polishing..." : "Enhance with AI"}
          </Button>
        )}
      </div>
    </div>
  );
}