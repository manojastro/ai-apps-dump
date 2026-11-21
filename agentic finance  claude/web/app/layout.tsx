import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SpreadLens AI",
  description: "Agentic financial spreading and analyst review",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
