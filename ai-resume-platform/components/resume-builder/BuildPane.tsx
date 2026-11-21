"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useResumeStore } from "@/store/resumeStore";
import { PasteContentTab } from "./PasteContentTab";
import { GuidedChatTab } from "./GuidedChatTab";
import { UploadTab } from "./UploadTab";
import { TemplatePicker } from "./TemplatePicker";
import { ResumeInsights } from "./ResumeInsights";

export function BuildPane() {
  const { inputMode, setInputMode } = useResumeStore();

  return (
    <div className="space-y-8">
      <ResumeInsights />

      <Tabs value={inputMode} onValueChange={(v) => setInputMode(v as "paste" | "chat" | "upload")}>
        <TabsList className="justify-start">
          <TabsTrigger value="paste">Paste</TabsTrigger>
          <TabsTrigger value="chat">Chat</TabsTrigger>
          <TabsTrigger value="upload">Upload</TabsTrigger>
        </TabsList>

        <TabsContent value="paste">
          <PasteContentTab />
        </TabsContent>
        <TabsContent value="chat">
          <GuidedChatTab />
        </TabsContent>
        <TabsContent value="upload">
          <UploadTab />
        </TabsContent>
      </Tabs>

      <TemplatePicker />
    </div>
  );
}