import type { Metadata } from "next";
import { Figtree, Fraunces } from "next/font/google";
import "./globals.css";
import { Masthead } from "@/components/Masthead";
import { DisclaimerBar } from "@/components/DisclaimerBar";

const display = Fraunces({
  subsets: ["latin"],
  variable: "--font-display",
});

const ui = Figtree({
  subsets: ["latin"],
  variable: "--font-ui",
});

export const metadata: Metadata = {
  title: "Aegis Plan India",
  description: "Research Indian investments. Understand the trade-offs. Leave with an actionable financial plan.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${display.variable} ${ui.variable} font-sans antialiased`}>
        <Masthead />
        <main className="mx-auto w-full max-w-6xl px-5 pb-12 pt-8">{children}</main>
        <DisclaimerBar />
      </body>
    </html>
  );
}
