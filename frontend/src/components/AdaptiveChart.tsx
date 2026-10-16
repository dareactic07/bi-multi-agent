"use client";

import React from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ChartSpec } from "@/types/agent";
import { formatValue } from "@/lib/utils";

const CHART_COLORS = [
  "#3b82f6", // Blue
  "#10b981", // Emerald
  "#f59e0b", // Amber
  "#8b5cf6", // Purple
  "#ec4899", // Pink
  "#06b6d4", // Cyan
  "#f97316", // Orange
];

interface AdaptiveChartProps {
  spec: ChartSpec;
}

export function AdaptiveChart({ spec }: AdaptiveChartProps) {
  const { chart_type, title, x_axis_key, y_axis_keys, data, summary } = spec;

  if (!data || data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-xl border border-dashed border-slate-700 bg-slate-900/50 p-6 text-slate-400">
        No dataset rows available for visualization.
      </div>
    );
  }

  // 1. Metric Card (Single KPI)
  if (chart_type === "metric_card") {
    const metricKey = y_axis_keys[0] || Object.keys(data[0] || {})[0];
    const metricVal = data[0]?.[metricKey];

    return (
      <div className="rounded-xl border border-slate-800 bg-gradient-to-br from-slate-900 to-slate-950 p-6 shadow-lg">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">{title}</h3>
        <div className="mt-3 text-4xl font-extrabold tracking-tight text-emerald-400">
          {formatValue(metricVal)}
        </div>
        {summary && <p className="mt-2 text-xs text-slate-400">{summary}</p>}
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-5 shadow-xl backdrop-blur">
      <div className="mb-4 flex flex-col justify-between gap-1 sm:flex-row sm:items-center">
        <div>
          <h3 className="text-base font-semibold text-slate-100">{title}</h3>
          {summary && <p className="text-xs text-slate-400">{summary}</p>}
        </div>
        <span className="self-start rounded-md border border-slate-700 bg-slate-800 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-slate-300">
          {chart_type}
        </span>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          {/* BAR CHART */}
          {chart_type === "bar" ? (
            <BarChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 25 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
              <XAxis
                dataKey={x_axis_key}
                stroke="#94a3b8"
                fontSize={11}
                tickLine={false}
                angle={-25}
                textAnchor="end"
                interval={0}
              />
              <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} tickFormatter={formatValue} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0f172a",
                  borderColor: "#334155",
                  borderRadius: "8px",
                  fontSize: "12px",
                  color: "#f8fafc",
                }}
                formatter={(val: any) => [formatValue(val), ""]}
              />
              <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }} />
              {y_axis_keys.map((key, idx) => (
                <Bar
                  key={key}
                  dataKey={key}
                  fill={CHART_COLORS[idx % CHART_COLORS.length]}
                  radius={[4, 4, 0, 0]}
                />
              ))}
            </BarChart>
          ) : /* LINE CHART */
          chart_type === "line" ? (
            <LineChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 25 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
              <XAxis
                dataKey={x_axis_key}
                stroke="#94a3b8"
                fontSize={11}
                tickLine={false}
                angle={-25}
                textAnchor="end"
              />
              <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} tickFormatter={formatValue} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0f172a",
                  borderColor: "#334155",
                  borderRadius: "8px",
                  fontSize: "12px",
                  color: "#f8fafc",
                }}
                formatter={(val: any) => [formatValue(val), ""]}
              />
              <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }} />
              {y_axis_keys.map((key, idx) => (
                <Line
                  key={key}
                  type="monotone"
                  dataKey={key}
                  stroke={CHART_COLORS[idx % CHART_COLORS.length]}
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: CHART_COLORS[idx % CHART_COLORS.length] }}
                />
              ))}
            </LineChart>
          ) : /* AREA CHART */
          chart_type === "area" ? (
            <AreaChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 25 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
              <XAxis dataKey={x_axis_key} stroke="#94a3b8" fontSize={11} tickLine={false} />
              <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} tickFormatter={formatValue} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0f172a",
                  borderColor: "#334155",
                  borderRadius: "8px",
                  fontSize: "12px",
                  color: "#f8fafc",
                }}
                formatter={(val: any) => [formatValue(val), ""]}
              />
              <Legend wrapperStyle={{ fontSize: "11px" }} />
              {y_axis_keys.map((key, idx) => (
                <Area
                  key={key}
                  type="monotone"
                  dataKey={key}
                  stroke={CHART_COLORS[idx % CHART_COLORS.length]}
                  fill={CHART_COLORS[idx % CHART_COLORS.length]}
                  fillOpacity={0.25}
                  strokeWidth={2}
                />
              ))}
            </AreaChart>
          ) : (
            /* PIE CHART */
            <PieChart>
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0f172a",
                  borderColor: "#334155",
                  borderRadius: "8px",
                  fontSize: "12px",
                  color: "#f8fafc",
                }}
                formatter={(val: any) => [formatValue(val), ""]}
              />
              <Legend wrapperStyle={{ fontSize: "11px" }} />
              <Pie
                data={data}
                dataKey={y_axis_keys[0]}
                nameKey={x_axis_key}
                cx="50%"
                cy="50%"
                outerRadius={85}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                labelLine={false}
              >
                {data.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                ))}
              </Pie>
            </PieChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}
