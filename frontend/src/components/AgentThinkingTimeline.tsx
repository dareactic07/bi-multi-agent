"use client";

import React from "react";
import { CheckCircle2, ChevronDown, ChevronUp, Loader2, Sparkles } from "lucide-react";
import { AgentStep } from "@/types/agent";

interface AgentThinkingTimelineProps {
  steps: AgentStep[];
  isStreaming?: boolean;
}

const STEP_ICONS: Record<string, string> = {
  orchestrator: "🔍",
  sql_engineer: "📝",
  sql_critic: "🛡️",
  executor: "⚡",
  storyteller: "📊",
};

const STEP_TITLES: Record<string, string> = {
  orchestrator: "Chief Orchestrator",
  sql_engineer: "SQL Engineer",
  sql_critic: "Data Critic & QA",
  executor: "DuckDB OLAP Engine",
  storyteller: "BI Storyteller",
};

export function AgentThinkingTimeline({ steps, isStreaming }: AgentThinkingTimelineProps) {
  const [isExpanded, setIsExpanded] = React.useState(true);

  if (!steps || steps.length === 0) return null;

  return (
    <div className="mb-4 overflow-hidden rounded-xl border border-slate-800 bg-slate-900/40 text-slate-200">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center justify-between px-4 py-2.5 text-left text-xs font-medium text-slate-300 hover:bg-slate-800/40"
      >
        <div className="flex items-center gap-2">
          {isStreaming ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin text-blue-400" />
          ) : (
            <Sparkles className="h-3.5 w-3.5 text-blue-400" />
          )}
          <span>Agent Pod Multi-Agent Reasoning ({steps.length} steps)</span>
        </div>
        {isExpanded ? (
          <ChevronUp className="h-3.5 w-3.5 text-slate-500" />
        ) : (
          <ChevronDown className="h-3.5 w-3.5 text-slate-500" />
        )}
      </button>

      {isExpanded && (
        <div className="space-y-2 border-t border-slate-800/80 p-3.5">
          {steps.map((step, idx) => {
            const isLatest = idx === steps.length - 1;
            const icon = STEP_ICONS[step.node] || "•";
            const title = STEP_TITLES[step.node] || step.node;

            return (
              <div key={idx} className="flex items-start gap-2.5 text-xs">
                <span className="text-sm select-none">{icon}</span>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-200">{title}</span>
                    {isLatest && isStreaming ? (
                      <span className="inline-flex items-center gap-1 text-[10px] font-medium text-blue-400">
                        <span className="h-1.5 w-1.5 rounded-full bg-blue-400 animate-ping" />
                        Running...
                      </span>
                    ) : (
                      <CheckCircle2 className="h-3 w-3 text-emerald-400" />
                    )}
                  </div>
                  <p className="mt-0.5 text-slate-400">{step.status_message}</p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
