import { redirect } from "next/navigation";
import { Shell } from "@/components/shell";
import { sessionToken } from "@/lib/server";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  if (!(await sessionToken())) redirect("/login");
  return <Shell>{children}</Shell>;
}
