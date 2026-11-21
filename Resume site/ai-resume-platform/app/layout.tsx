import type { Metadata } from "next";
import { Navbar } from "@/components/shared/Navbar";
import { Footer } from "@/components/shared/Footer";
import { ToastContainer } from "@/components/shared/Toast";
import { SessionProvider } from "@/components/shared/SessionProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: "ResumeAI — ATS Resume Builder & Job Trends",
  description:
    "Build ATS-friendly resumes with AI and explore live job insights for Indian job seekers",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <body className="flex min-h-full flex-col font-sans text-[#1d1d1f] antialiased">
        <SessionProvider>
          <Navbar />
          <main className="flex-1">{children}</main>
          <Footer />
          <ToastContainer />
        </SessionProvider>
      </body>
    </html>
  );
}
