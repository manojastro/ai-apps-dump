"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { Account360, Forecast } from "@/lib/types";
import { formatCompact, formatDate, formatMoney } from "@/lib/utils";

const axis = { fontSize: 11, fill: "var(--chart-axis)" };
const tooltipStyle = {
  background: "var(--chart-surface)",
  border: "1px solid var(--chart-grid)",
  borderRadius: 8,
  fontSize: 12,
  color: "hsl(var(--foreground))",
};

/** Labels use normal text colour. The coloured dot beside them carries the identity. */
const legendText = (value: string) => <span style={{ color: "hsl(var(--foreground))" }}>{value}</span>;

/** Same unit on both series, so one shared axis is honest. */
export function ForecastByTeamChart({ teams }: { teams: Forecast["by_team"] }) {
  const data = teams.map((t) => ({ team: t.team, Expected: t.expected, "Rep commit": t.rep_commit, low: t.low, high: t.high }));
  return (
    <div className="h-64" role="img" aria-label="Expected forecast compared with rep commit, by team">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} barGap={2} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
          <XAxis dataKey="team" tick={axis} axisLine={false} tickLine={false} />
          <YAxis tick={axis} axisLine={false} tickLine={false} tickFormatter={formatCompact} width={62} />
          <Tooltip
            cursor={{ fill: "hsl(var(--muted))", opacity: 0.5 }}
            contentStyle={tooltipStyle}
            formatter={(value: number, name: string) => [formatMoney(value), name]}
            labelFormatter={(label, payload) => {
              const row = payload?.[0]?.payload;
              return row ? `${label} (range ${formatCompact(row.low)} to ${formatCompact(row.high)})` : label;
            }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} iconType="circle" iconSize={8} formatter={legendText} />
          <Bar dataKey="Expected" fill="var(--series-1)" radius={[4, 4, 0, 0]} maxBarSize={36} isAnimationActive={false} />
          <Bar dataKey="Rep commit" fill="var(--series-2)" radius={[4, 4, 0, 0]} maxBarSize={36} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/** Active users against purchased seats: same unit, one axis. */
export function UsageChart({ data }: { data: Account360["usage_trend"] }) {
  const rows = data.map((point) => ({ week: point.week, "Active users": point.active_users, Seats: point.seats }));
  return (
    <div className="h-56" role="img" aria-label="Weekly active users compared with purchased seats">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={rows} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
          <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
          <XAxis
            dataKey="week"
            tick={axis}
            axisLine={false}
            tickLine={false}
            minTickGap={48}
            tickFormatter={(value: string) => new Date(`${value}T00:00:00`).toLocaleDateString("en-US", { month: "short" })}
          />
          <YAxis tick={axis} axisLine={false} tickLine={false} width={44} />
          <Tooltip contentStyle={tooltipStyle} labelFormatter={(label: string) => `Week of ${formatDate(label)}`} />
          <Legend wrapperStyle={{ fontSize: 12 }} iconType="circle" iconSize={8} formatter={legendText} />
          <Line dataKey="Active users" stroke="var(--series-1)" strokeWidth={2} dot={false} activeDot={{ r: 4 }} isAnimationActive={false} />
          <Line dataKey="Seats" type="stepAfter" stroke="var(--series-2)" strokeWidth={2} strokeDasharray="4 3" dot={false} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
