"use client";

import type { ReactNode } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export const RISK_COLORS: Record<string, string> = {
  critical: "var(--risk-critical)",
  high: "var(--risk-high)",
  medium: "var(--risk-medium)",
  low: "var(--risk-low)",
  none: "var(--risk-unknown)",
  unknown: "var(--risk-unknown)",
};

const axis = { stroke: "var(--muted-foreground)", fontSize: 11, tickLine: false, axisLine: false } as const;
const tooltipStyle = {
  contentStyle: { background: "var(--popover)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12, color: "var(--popover-foreground)" },
  cursor: { fill: "var(--muted)", opacity: 0.4 },
};

export function ChartCard({ title, description, children, height = 240 }: { title: string; description?: string; children: ReactNode; height?: number }) {
  return (
    <Card className="gap-2">
      <CardHeader>
        <CardTitle className="text-sm">{title}</CardTitle>
        {description && <CardDescription className="text-xs">{description}</CardDescription>}
      </CardHeader>
      <CardContent>
        <div style={{ height }}>{children}</div>
      </CardContent>
    </Card>
  );
}

export function SimpleBar({ data, x, bars, colors, layout = "horizontal", stacked = false }: {
  data: Record<string, unknown>[];
  x: string;
  bars: { key: string; label: string; color: string }[];
  colors?: (row: Record<string, unknown>) => string;
  layout?: "horizontal" | "vertical";
  stacked?: boolean;
}) {
  const vertical = layout === "vertical";
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} layout={vertical ? "vertical" : "horizontal"} margin={{ top: 4, right: 8, bottom: 0, left: vertical ? 8 : -16 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={vertical} horizontal={!vertical} />
        {vertical ? <XAxis type="number" {...axis} allowDecimals={false} /> : <XAxis dataKey={x} {...axis} />}
        {vertical ? <YAxis type="category" dataKey={x} {...axis} width={150} /> : <YAxis {...axis} allowDecimals={false} />}
        <Tooltip {...tooltipStyle} />
        {bars.length > 1 && <Legend wrapperStyle={{ fontSize: 11 }} />}
        {bars.map((b) => (
          <Bar key={b.key} dataKey={b.key} name={b.label} fill={b.color} radius={stacked ? 0 : 4} stackId={stacked ? "s" : undefined} maxBarSize={36}>
            {colors && data.map((row, i) => <Cell key={i} fill={colors(row)} />)}
          </Bar>
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

export function SimpleArea({ data, x, areas }: { data: Record<string, unknown>[]; x: string; areas: { key: string; label: string; color: string }[] }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -16 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
        <XAxis dataKey={x} {...axis} tickFormatter={(v: string) => v.slice(5)} />
        <YAxis {...axis} allowDecimals={false} />
        <Tooltip {...tooltipStyle} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        {areas.map((a) => (
          <Area key={a.key} type="monotone" dataKey={a.key} name={a.label} stroke={a.color} fill={a.color} fillOpacity={0.15} strokeWidth={2} />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function Donut({ data, nameKey, valueKey, colorOf }: { data: Record<string, unknown>[]; nameKey: string; valueKey: string; colorOf: (name: string) => string }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie data={data} dataKey={valueKey} nameKey={nameKey} innerRadius="58%" outerRadius="85%" paddingAngle={2} stroke="var(--card)">
          {data.map((row, i) => <Cell key={i} fill={colorOf(String(row[nameKey]))} />)}
        </Pie>
        <Tooltip {...tooltipStyle} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
      </PieChart>
    </ResponsiveContainer>
  );
}
