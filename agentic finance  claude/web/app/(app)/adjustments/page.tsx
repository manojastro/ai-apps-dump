"use client";
import { useSession } from "@/components/shell";
import { AdjustmentHistory } from "@/components/review-panels";
import { Card, Spinner } from "@/components/ui";
import { useApi } from "@/lib/hooks";

type Adj = Parameters<typeof AdjustmentHistory>[0]["items"][number];

export default function AdjustmentsPage() {
  const { workspaceId } = useSession();
  const { data } = useApi<Adj[]>(workspaceId ? `/workspaces/${workspaceId}/adjustments` : null);
  return <Card title="Adjustment history (all spreads in this workspace)">{data ? <AdjustmentHistory items={data} /> : <Spinner />}</Card>;
}
