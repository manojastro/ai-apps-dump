"use client";

import { useCallback, useMemo, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { LoadingButton } from "@/components/shared/LoadingButton";
import { ChatStepper } from "./ChatStepper";
import { useResumeStore } from "@/store/resumeStore";
import { useToastStore } from "@/store/toastStore";
import type { ResumeData } from "@/lib/resumeSchema";
import { slideDir, fadeOnly } from "@/lib/motion";

const STEPS = [
  { key: "fullName", label: "What's your name?", type: "input" as const },
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
    case "fullName":
      updated.personalInfo.fullName = value;
      break;
    case "email":
      updated.personalInfo.email = value;
      break;
    case "phone":
      updated.personalInfo.phone = value;
      break;
    case "location":
      updated.personalInfo.location = value;
      break;
    case "targetRole":
      updated.targetRole = value;
      break;
    case "summary":
      updated.summary = value;
      break;
    case "experience":
      updated.experience = [
        {
          company: "",
          role: "",
          location: "",
          startDate: "",
          endDate: "",
          current: false,
          bullets: value.split("\n").filter(Boolean),
        },
      ];
      break;
    case "education":
      updated.education = [
        {
          institution: value.split(",")[0]?.trim() || value,
          degree: value.split(",")[1]?.trim() || "",
          field: "",
          startDate: "",
          endDate: "",
        },
      ];
      break;
    case "skills": {
      const items = value
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      updated.skills = { technical: items, soft: [] };
      break;
    }
    case "certifications":
      if (value.trim())
        updated.certifications = [{ name: value, issuer: "", date: "" }];
      break;
  }
  return updated;
}

export function GuidedChatTab() {
  const {
    chatStep,
    setChatStep,
    chatAnswers,
    setChatAnswer,
    resume,
    setResume,
    isEnhancing,
    setIsEnhancing,
    setEnhanceError,
    targetJobDescription,
    setMobilePane,
  } = useResumeStore();
  const addToast = useToastStore((s) => s.addToast);
  const reduce = useReducedMotion();
  const [dir, setDir] = useState<1 | -1>(1);
  const [enhanceSuccess, setEnhanceSuccess] = useState(false);

  const currentStep = STEPS[chatStep];
  const isLastStep = chatStep >= STEPS.length - 1;
  const currentValue = chatAnswers[currentStep?.key] ?? "";

  const handleNext = useCallback(() => {
    if (!currentStep || !currentValue.trim()) return;
    setResume(applyChatAnswer(resume, currentStep.key, currentValue));
    if (!isLastStep) {
      setDir(1);
      setChatStep(chatStep + 1);
    }
  }, [
    currentStep,
    currentValue,
    resume,
    setResume,
    isLastStep,
    chatStep,
    setChatStep,
  ]);

  const handleBack = useCallback(() => {
    if (chatStep <= 0) return;
    setDir(-1);
    setChatStep(chatStep - 1);
  }, [chatStep, setChatStep]);

  const handleEnhance = useCallback(async () => {
    setIsEnhancing(true);
    setEnhanceError(null);
    setEnhanceSuccess(false);
    setMobilePane("preview");
    const rawText = STEPS.map(
      (s) => `${s.label}\n${chatAnswers[s.key] || ""}`
    ).join("\n\n");
    try {
      const res = await fetch("/api/resume/enhance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          rawText,
          targetJobDescription: targetJobDescription || undefined,
          existingResumeJson: resume,
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || "Enhancement failed");
      }
      setResume(await res.json(), true);
      setEnhanceSuccess(true);
      addToast("Your resume is ready to review", "success");
    } catch (e) {
      setEnhanceError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setIsEnhancing(false);
    }
  }, [
    chatAnswers,
    targetJobDescription,
    resume,
    setIsEnhancing,
    setEnhanceError,
    setResume,
    addToast,
    setMobilePane,
  ]);

  const canEnhance = useMemo(
    () =>
      !!(chatAnswers.fullName && (chatAnswers.experience || chatAnswers.education)),
    [chatAnswers]
  );

  if (!currentStep) return null;

  return (
    <div className="space-y-7">
      <ChatStepper total={STEPS.length} current={chatStep} />

      <AnimatePresence mode="wait" custom={dir}>
        <motion.div
          key={currentStep.key}
          custom={dir}
          variants={reduce ? fadeOnly : slideDir(dir)}
          initial="initial"
          animate="animate"
          exit="exit"
          className="space-y-5"
        >
          <p className="text-[21px] font-medium leading-snug tracking-tight text-[#1d1d1f]">
            {currentStep.label}
          </p>

          {currentStep.type === "textarea" ? (
            <Textarea
              id="chat-input"
              aria-label={currentStep.label}
              className="min-h-[140px]"
              value={currentValue}
              onChange={(e) => setChatAnswer(currentStep.key, e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && e.ctrlKey) handleNext();
              }}
            />
          ) : (
            <Input
              id="chat-input"
              aria-label={currentStep.label}
              value={currentValue}
              onChange={(e) => setChatAnswer(currentStep.key, e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleNext();
              }}
            />
          )}
        </motion.div>
      </AnimatePresence>

      <div className="flex items-center gap-4">
        {chatStep > 0 && (
          <Button variant="ghost" onClick={handleBack}>
            Back
          </Button>
        )}
        {!isLastStep ? (
          <Button onClick={handleNext} disabled={!currentValue.trim()}>
            Continue
          </Button>
        ) : (
          <LoadingButton
            size="lg"
            onClick={handleEnhance}
            disabled={!canEnhance}
            loading={isEnhancing}
            success={enhanceSuccess}
            successLabel="Ready"
            iconHoverShift="right"
          >
            Enhance with AI
          </LoadingButton>
        )}
      </div>
    </div>
  );
}
