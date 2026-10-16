"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  BarChart3,
  Bot,
  Compass,
  Database,
  ExternalLink,
  MessageSquare,
  RotateCcw,
  Send,
  Sparkles,
  TrendingUp,
  User,
} from "lucide-react";
import { AdaptiveChart } from "@/components/AdaptiveChart";
import { AgentThinkingTimeline } from "@/components/AgentThinkingTimeline";
import { MetricCardsGrid } from "@/components/MetricCardsGrid";
import { SQLInspector } from "@/components/SQLInspector";
import { useAgentChat } from "@/hooks/useAgentChat";

const SUGGESTED_QUERIES = [
  "What were our top 5 product categories by revenue in 2017?",
  "Show monthly order volume trend over time",
  "Which 5 Brazilian states have the highest order volume?",
  "Break down orders by payment type and total payment value",
  "Count orders by order status (delivered, shipped, canceled)",
];

export default function Home() {
  const [inputValue, setInputValue] = useState("");
  const { messages, isLoading, sendMessage, clearChat } = useAgentChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;
    sendMessage(inputValue);
    setInputValue("");
  };

  const handleSuggestionClick = (query: string) => {
    if (isLoading) return;
    sendMessage(query);
  };

  return (
    <div className="flex min-h-screen flex-col bg-[#070b14] text-slate-100">
      {/* 1. Header Navigation */}
      <header className="sticky top-0 z-30 border-b border-slate-800/80 bg-[#070b14]/90 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 shadow-md shadow-blue-500/20">
              <BarChart3 className="h-5 w-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-sm font-bold tracking-tight text-white sm:text-base">
                  Olist Autonomous BI Agent
                </h1>
                <span className="rounded-full border border-blue-500/30 bg-blue-500/10 px-2 py-0.5 text-[10px] font-semibold text-blue-400">
                  LangGraph + DuckDB
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                100,000 real Brazilian e-commerce orders analyzed in milliseconds
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="hidden items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-emerald-400 sm:inline-flex">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              Engine Online (99,441 records)
            </span>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1 rounded-lg border border-slate-800 bg-slate-900 px-2.5 py-1.5 text-xs font-medium text-slate-300 transition hover:bg-slate-800 hover:text-white"
            >
              <span>Swagger API</span>
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        </div>
      </header>

      {/* 2. Main Content Body */}
      <main className="mx-auto flex w-full max-w-7xl flex-1 flex-col px-4 py-6 sm:px-6">
        {/* KPI Stats Grid */}
        <div className="mb-6">
          <MetricCardsGrid />
        </div>

        {/* Chat / Analysis Area */}
        <div className="flex flex-1 flex-col rounded-2xl border border-slate-800/80 bg-slate-950/50 shadow-2xl backdrop-blur">
          {/* Header inside chat box */}
          <div className="flex items-center justify-between border-b border-slate-800/80 px-4 py-3">
            <div className="flex items-center gap-2 text-xs font-medium text-slate-300">
              <Bot className="h-4 w-4 text-blue-400" />
              <span>Multi-Agent Collaborative Conversation</span>
            </div>
            {messages.length > 0 && (
              <button
                onClick={clearChat}
                className="flex items-center gap-1 rounded px-2 py-1 text-xs text-slate-400 hover:bg-slate-900 hover:text-slate-200"
              >
                <RotateCcw className="h-3 w-3" />
                Clear Chat
              </button>
            )}
          </div>

          {/* Messages List */}
          <div className="flex-1 space-y-6 overflow-y-auto p-4 sm:p-6">
            {messages.length === 0 ? (
              <div className="my-auto flex flex-col items-center justify-center py-12 text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-500/10 text-blue-400 ring-1 ring-blue-500/20">
                  <Sparkles className="h-6 w-6" />
                </div>
                <h2 className="mt-4 text-lg font-semibold text-white">
                  Ask any business intelligence question
                </h2>
                <p className="mt-1 max-w-md text-xs text-slate-400">
                  The Chief Orchestrator, SQL Engineer, Data Critic, and BI Storyteller will prune the
                  schema, validate safe DuckDB queries, and stream interactive visualizations.
                </p>

                {/* Query Suggestions */}
                <div className="mt-8 flex w-full max-w-2xl flex-col gap-2">
                  <span className="text-[11px] font-medium uppercase tracking-wider text-slate-500">
                    Recommended Questions:
                  </span>
                  <div className="flex flex-wrap justify-center gap-2">
                    {SUGGESTED_QUERIES.map((query, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleSuggestionClick(query)}
                        className="rounded-lg border border-slate-800 bg-slate-900/80 px-3 py-2 text-left text-xs text-slate-300 transition hover:border-blue-500/50 hover:bg-slate-800/80 hover:text-white"
                      >
                        {query}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex gap-3 ${
                    message.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  {message.role === "assistant" && (
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-600/20 border border-blue-500/30 text-blue-400">
                      <Bot className="h-4 w-4" />
                    </div>
                  )}

                  <div
                    className={`max-w-3xl rounded-2xl px-4 py-3.5 text-sm ${
                      message.role === "user"
                        ? "bg-blue-600 text-white shadow-md shadow-blue-600/10"
                        : "w-full border border-slate-800/90 bg-slate-900/60 text-slate-200"
                    }`}
                  >
                    {/* Timestamp / User header */}
                    <div className="mb-1 flex items-center justify-between text-[11px] text-slate-400">
                      <span className="font-medium text-slate-300">
                        {message.role === "user" ? "You" : "BI Multi-Agent Pod"}
                      </span>
                      <span>{message.timestamp}</span>
                    </div>

                    {/* Agent Thinking Timeline (Multi-Agent steps) */}
                    {message.role === "assistant" && (
                      <AgentThinkingTimeline
                        steps={message.steps}
                        isStreaming={message.isStreaming}
                      />
                    )}

                    {/* Main textual answer / insights */}
                    {message.content && (
                      <div className="prose prose-invert max-w-none text-xs sm:text-sm leading-relaxed space-y-2 whitespace-pre-wrap">
                        {message.content}
                      </div>
                    )}

                    {/* Dynamic Recharts Chart */}
                    {message.chart_spec && (
                      <div className="mt-4">
                        <AdaptiveChart spec={message.chart_spec} />
                      </div>
                    )}

                    {/* SQL Inspector & Data Drawer */}
                    {message.role === "assistant" && (
                      <SQLInspector
                        sql={message.generated_sql}
                        result={message.query_result}
                      />
                    )}
                  </div>

                  {message.role === "user" && (
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-800 text-slate-300">
                      <User className="h-4 w-4" />
                    </div>
                  )}
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* 3. Input Control Bar */}
          <div className="border-t border-slate-800/80 p-3 sm:p-4 bg-slate-900/40 rounded-b-2xl">
            <form onSubmit={handleSubmit} className="flex items-center gap-2">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Ask about revenue, categories, delivery times, customer retention..."
                disabled={isLoading}
                className="flex-1 rounded-xl border border-slate-800 bg-slate-950 px-4 py-3 text-sm text-white placeholder-slate-500 shadow-inner outline-none transition focus:border-blue-500/80 focus:ring-1 focus:ring-blue-500/80 disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={isLoading || !inputValue.trim()}
                className="flex h-11 items-center gap-2 rounded-xl bg-blue-600 px-5 text-sm font-semibold text-white shadow-lg shadow-blue-600/25 transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <span>Ask</span>
                <Send className="h-4 w-4" />
              </button>
            </form>
          </div>
        </div>
      </main>

      {/* 4. Footer */}
      <footer className="border-t border-slate-800/60 py-4 text-center text-xs text-slate-500">
        Autonomous Business Intelligence Multi-Agent System • Powered by LangGraph, DuckDB & PostgreSQL 16
      </footer>
    </div>
  );
}
