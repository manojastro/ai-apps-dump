import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Navbar } from "@/components/shared/Navbar";
import { AmbientBackground } from "@/components/shared/AmbientBackground";
import { Footer } from "@/components/shared/Footer";
import { ToastContainer } from "@/components/shared/Toast";
import { SessionProvider } from "@/components/shared/SessionProvider";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "ResumeAI — ATS Resume Builder & Job Trends",
  description:
    "Build ATS-friendly resumes with AI and explore real-time job trends in India",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} h-full`}>
      <body className="min-h-full flex flex-col text-[#1d1d1f] antialiased">
        <AmbientBackground />
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