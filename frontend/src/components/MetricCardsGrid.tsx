"use client";

import React from "react";
import { Database, Package, ShoppingBag, Store, Users, Zap } from "lucide-react";

export function MetricCardsGrid() {
  const kpis = [
    {
      title: "Total Orders",
      value: "99,441",
      detail: "Delivered & analyzed",
      icon: ShoppingBag,
      color: "text-blue-400",
      bg: "bg-blue-500/10",
    },
    {
      title: "Unique Customers",
      value: "96,096",
      detail: "Across 27 Brazilian states",
      icon: Users,
      color: "text-emerald-400",
      bg: "bg-emerald-500/10",
    },
    {
      title: "Active Sellers",
      value: "3,095",
      detail: "Merchant network",
      icon: Store,
      color: "text-amber-400",
      bg: "bg-amber-500/10",
    },
    {
      title: "Product Catalog",
      value: "32,951",
      detail: "English translated categories",
      icon: Package,
      color: "text-purple-400",
      bg: "bg-purple-500/10",
    },
    {
      title: "Execution Engine",
      value: "DuckDB + PG16",
      detail: "In-memory zero-copy OLAP",
      icon: Zap,
      color: "text-cyan-400",
      bg: "bg-cyan-500/10",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {kpis.map((kpi, idx) => {
        const Icon = kpi.icon;
        return (
          <div
            key={idx}
            className="rounded-xl border border-slate-800/80 bg-slate-900/60 p-3.5 shadow-sm backdrop-blur transition hover:border-slate-700"
          >
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400">
                {kpi.title}
              </span>
              <div className={`rounded-md p-1.5 ${kpi.bg}`}>
                <Icon className={`h-3.5 w-3.5 ${kpi.color}`} />
              </div>
            </div>
            <div className="mt-2 text-xl font-bold tracking-tight text-white">{kpi.value}</div>
            <p className="mt-0.5 text-[11px] text-slate-400">{kpi.detail}</p>
          </div>
        );
      })}
    </div>
  );
}
