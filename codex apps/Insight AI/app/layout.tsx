import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "ProductionLens | Investigation & assurance", description: "Evidence-backed production investigations and agent release evaluation" };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html>; }
