import Link from "next/link";
import { api } from "../../api";
import { RCAEditor } from "../../components";
import type { Investigation } from "../../types";

export default async function RCAPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const investigation = await api<Investigation>(`/api/v1/incidents/${id}/investigation`);
  return <><header className="page-head"><div><div className="eyebrow">Citation-gated postmortem</div><h1>Final RCA editor</h1><p>Every factual bullet must retain at least one immutable evidence ID.</p></div><Link href={`/investigations/${id}`}>Back to investigation</Link></header><RCAEditor investigation={investigation}/></>;
}

