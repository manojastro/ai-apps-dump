"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { UsageChart } from "@/components/charts";
import { CitationChip } from "@/components/citations";
import { ChurnBand, DealBand, EmptyNote, ErrorNote, HealthBadge, LoadingBlock, Meter, PageHeader, ReasonChips, StatTile, StatusBadge } from "@/components/shared";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, Table, Td, Th } from "@/components/ui/primitives";
import { useApi } from "@/lib/api";
import type { Account360 } from "@/lib/types";
import { formatCompact, formatDate, formatMoney, formatPercent, titleCase } from "@/lib/utils";

export default function AccountPage() {
  const { id } = useParams<{ id: string }>();
  const { data, error, loading } = useApi<Account360>(`/accounts/${id}/360`);

  if (loading) return <LoadingBlock rows={10} />;
  if (error) return <ErrorNote message={error.status === 404 ? "Account not found, or it belongs to another team." : error.message} />;
  if (!data) return null;

  const { account } = data;
  const current = data.subscriptions[0];
  const openTickets = data.tickets.filter((t) => !t.resolved_at).length;
  const overdue = data.invoices.filter((i) => i.status === "overdue").length;

  return (
    <>
      <PageHeader
        title={account.name}
        description={`${titleCase(account.segment)} · ${account.region} · ${account.industry ?? "Industry unknown"} · Owner ${account.owner_name ?? "unassigned"}`}
      >
        <div className="flex items-center gap-2">
          {account.status === "churned" ? <StatusBadge tone="neutral" label={`Churned ${formatDate(account.churned_at)}`} /> : <HealthBadge status={account.health_status} />}
        </div>
      </PageHeader>

      <div className="mb-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile label="ARR" value={formatCompact(account.arr)} detail={current ? `${current.seats} seats` : undefined} />
        <StatTile label="Churn risk (90 days)" value={formatPercent(account.p_churn)} detail={<ChurnBand band={account.churn_band} />} />
        <StatTile label="Renewal" value={formatDate(current?.renewal_date)} detail={current ? titleCase(current.status) : undefined} />
        <StatTile label="Open tickets" value={String(openTickets)} detail={`${overdue} overdue invoices`} />
      </div>

      <div className="mb-4 grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Usage trend</CardTitle>
            <CardDescription>Average daily active users per week, against purchased seats</CardDescription>
          </CardHeader>
          <CardContent>{data.usage_trend.length ? <UsageChart data={data.usage_trend} /> : <EmptyNote message="No usage data." />}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Open risks</CardTitle>
          </CardHeader>
          <CardContent>
            {data.open_risks.length === 0 && <p className="text-sm text-muted-foreground">No open risks.</p>}
            <ul className="space-y-2 text-sm">
              {data.open_risks.map((risk) => (
                <li key={`${risk.type}-${risk.cite}`}>{risk.text} <CitationChip cite={risk.cite} /></li>
              ))}
            </ul>
            {data.churn_reasons.length > 0 && (
              <div className="mt-3 border-t pt-3">
                <p className="mb-1.5 text-xs font-medium text-muted-foreground">Churn model reasons</p>
                <ReasonChips reasons={data.churn_reasons} limit={4} />
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="mb-4">
        <CardHeader><CardTitle>Deals</CardTitle></CardHeader>
        <CardContent className="p-0 pb-2">
          {data.deals.length === 0 ? <EmptyNote message="No deals." /> : (
            <Table>
              <thead>
                <tr>
                  <Th>Deal</Th><Th className="text-right">Amount</Th><Th>Stage</Th><Th>Close date</Th><Th>Win probability</Th><Th>Risk</Th>
                </tr>
              </thead>
              <tbody>
                {data.deals.map((deal) => (
                  <tr key={deal.id}>
                    <Td><Link href={`/deals/${deal.id}`} className="font-medium hover:underline">{deal.name}</Link></Td>
                    <Td className="text-right tabular-nums">{formatMoney(deal.amount)}</Td>
                    <Td>{titleCase(deal.stage)}</Td>
                    <Td className="whitespace-nowrap">{formatDate(deal.closed_at ?? deal.close_date)}</Td>
                    <Td>{deal.outcome ? <span className="text-muted-foreground">Closed</span> : <Meter value={deal.p_win} />}</Td>
                    <Td>{deal.outcome ? null : <DealBand band={deal.risk_band} />}</Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </CardContent>
      </Card>

      <div className="mb-4 grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Timeline</CardTitle>
            <CardDescription>Most recent events across every system</CardDescription>
          </CardHeader>
          <CardContent className="max-h-96 overflow-y-auto">
            <ol className="space-y-2 text-sm">
              {data.timeline.map((event, index) => (
                <li key={`${event.cite}-${index}`} className="flex gap-3">
                  <time className="w-24 shrink-0 text-xs text-muted-foreground">{formatDate(event.date)}</time>
                  <span className="min-w-0">{event.text} <CitationChip cite={event.cite} /></span>
                </li>
              ))}
            </ol>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Tickets ({data.tickets.length})</CardTitle></CardHeader>
          <CardContent className="max-h-96 overflow-y-auto">
            {data.tickets.length === 0 && <EmptyNote message="No tickets." />}
            <ul className="divide-y text-sm">
              {data.tickets.map((ticket) => (
                <li key={ticket.id} className="py-2">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium">{ticket.subject}</span>
                    <StatusBadge tone={ticket.severity <= 1 ? "critical" : ticket.severity === 2 ? "serious" : "neutral"} label={`Sev ${ticket.severity}`} />
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Opened {formatDate(ticket.opened_at)} · {ticket.resolved_at ? `Resolved ${formatDate(ticket.resolved_at)}` : "Open"}
                  </p>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Invoices</CardTitle></CardHeader>
          <CardContent className="max-h-80 overflow-y-auto p-0 pb-2">
            <Table>
              <thead><tr><Th>Due</Th><Th className="text-right">Amount</Th><Th>Paid</Th><Th>Status</Th></tr></thead>
              <tbody>
                {data.invoices.map((invoice) => (
                  <tr key={invoice.id}>
                    <Td>{formatDate(invoice.due_date)}</Td>
                    <Td className="text-right tabular-nums">{formatMoney(invoice.amount)}</Td>
                    <Td>{formatDate(invoice.paid_date)}</Td>
                    <Td><StatusBadge tone={invoice.status === "overdue" ? "critical" : invoice.status === "paid" ? "good" : "neutral"} label={titleCase(invoice.status)} /></Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Contacts</CardTitle></CardHeader>
          <CardContent className="max-h-80 overflow-y-auto p-0 pb-2">
            <Table>
              <thead><tr><Th>Name</Th><Th>Title</Th><Th>Role</Th><Th>Last seen</Th></tr></thead>
              <tbody>
                {data.contacts.map((contact) => (
                  <tr key={contact.id}>
                    <Td className="whitespace-nowrap">{contact.full_name}</Td>
                    <Td>{contact.title ?? "-"}</Td>
                    <Td className="whitespace-nowrap">{[contact.is_executive && "Executive", contact.is_champion && "Champion"].filter(Boolean).join(", ") || "-"}</Td>
                    <Td className="whitespace-nowrap">{formatDate(contact.last_seen)}</Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
