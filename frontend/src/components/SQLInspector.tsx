"use client";

import React, { useState } from "react";
import { Check, ChevronDown, ChevronUp, Code2, Copy, Download, Table2 } from "lucide-react";
import { QueryResult } from "@/types/agent";
import { exportToCsv, formatValue } from "@/lib/utils";

interface SQLInspectorProps {
  sql?: string;
  result?: QueryResult;
}

export function SQLInspector({ sql, result }: SQLInspectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<"sql" | "data">("sql");
  const [copied, setCopied] = useState(false);

  if (!sql && !result) return null;

  const handleCopy = () => {
    if (sql) {
      navigator.clipboard.writeText(sql);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleExportCsv = () => {
    if (result && result.rows.length) {
      exportToCsv("olist_query_export", result.columns, result.rows);
    }
  };

  return (
    <div className="mt-3 overflow-hidden rounded-xl border border-slate-800 bg-slate-950/70 text-slate-200 shadow-inner">
      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 px-4 py-2.5">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 text-xs font-medium text-slate-300 hover:text-white"
        >
          <Code2 className="h-4 w-4 text-blue-400" />
          <span>Analytical SQL & Query Execution Data</span>
          {isOpen ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5 text-slate-500" />}
        </button>

        <div className="flex items-center gap-2">
          {result && (
            <>
              <span className="rounded bg-emerald-950/60 px-2 py-0.5 text-[11px] font-mono font-medium text-emerald-400 border border-emerald-800/40">
                ⚡ {result.execution_time_ms} ms
              </span>
              <span className="rounded bg-blue-950/60 px-2 py-0.5 text-[11px] font-mono font-medium text-blue-400 border border-blue-800/40">
                {result.row_count} rows
              </span>
            </>
          )}

          {isOpen && (
            <div className="flex items-center gap-1">
              <button
                onClick={() => setActiveTab("sql")}
                className={`rounded px-2.5 py-1 text-xs font-medium transition ${
                  activeTab === "sql"
                    ? "bg-slate-800 text-white"
                    : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
                }`}
              >
                SQL
              </button>
              {result && result.rows.length > 0 && (
                <button
                  onClick={() => setActiveTab("data")}
                  className={`rounded px-2.5 py-1 text-xs font-medium transition ${
                    activeTab === "data"
                      ? "bg-slate-800 text-white"
                      : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
                  }`}
                >
                  <Table2 className="mr-1 inline h-3 w-3" />
                  Table
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Expanded content */}
      {isOpen && (
        <div className="p-4">
          {activeTab === "sql" && sql && (
            <div className="relative">
              <div className="absolute right-2 top-2">
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1 rounded border border-slate-700 bg-slate-800/90 px-2 py-1 text-[11px] font-medium text-slate-300 hover:bg-slate-700 hover:text-white"
                >
                  {copied ? (
                    <>
                      <Check className="h-3 w-3 text-emerald-400" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="h-3 w-3" />
                      Copy SQL
                    </>
                  )}
                </button>
              </div>
              <pre className="overflow-x-auto rounded-lg bg-slate-900/90 p-4 font-mono text-xs leading-relaxed text-blue-300 border border-slate-800">
                {sql}
              </pre>
            </div>
          )}

          {activeTab === "data" && result && (
            <div>
              <div className="mb-2 flex items-center justify-between">
                <span className="text-xs text-slate-400">
                  Showing top {Math.min(result.rows.length, 50)} of {result.row_count} records
                </span>
                <button
                  onClick={handleExportCsv}
                  className="flex items-center gap-1 rounded border border-slate-700 bg-slate-800 px-2.5 py-1 text-xs font-medium text-slate-200 hover:bg-slate-700 hover:text-white"
                >
                  <Download className="h-3 w-3" />
                  Export CSV
                </button>
              </div>
              <div className="max-h-72 overflow-auto rounded-lg border border-slate-800">
                <table className="w-full text-left text-xs">
                  <thead className="sticky top-0 bg-slate-800/90 text-slate-300 backdrop-blur">
                    <tr>
                      {result.columns.map((col) => (
                        <th key={col} className="px-3 py-2 font-semibold">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 bg-slate-900/40">
                    {result.rows.slice(0, 50).map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30">
                        {result.columns.map((col) => (
                          <td key={col} className="px-3 py-1.5 font-mono text-slate-300">
                            {formatValue(row[col])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
