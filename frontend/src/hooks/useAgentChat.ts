"use client";

import { useState } from "react";
import { AgentStep, ChatMessage } from "@/types/agent";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export function useAgentChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async (queryText: string) => {
    if (!queryText.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: "user-" + Date.now(),
      role: "user",
      content: queryText,
      steps: [],
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    const assistantId = "assistant-" + Date.now();
    const initialAssistantMessage: ChatMessage = {
      id: assistantId,
      role: "assistant",
      content: "",
      steps: [],
      isStreaming: true,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage, initialAssistantMessage]);
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: queryText }),
      });

      if (!response.ok) {
        throw new Error(`HTTP Error ${response.status}: ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error("ReadableStream is not supported by this browser.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const block of lines) {
          if (!block.trim()) continue;

          let eventType = "message";
          let dataStr = "";

          const blockLines = block.split("\n");
          for (const line of blockLines) {
            if (line.startsWith("event:")) {
              eventType = line.replace("event:", "").trim();
            } else if (line.startsWith("data:")) {
              dataStr += line.replace("data:", "").trim();
            }
          }

          if (!dataStr) continue;

          try {
            const data = JSON.parse(dataStr);

            if (eventType === "status") {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? {
                        ...m,
                        steps: [
                          ...m.steps,
                          {
                            node: data.step || "init",
                            status_message: data.message || "Initializing...",
                            timestamp: new Date().toLocaleTimeString(),
                          },
                        ],
                      }
                    : m
                )
              );
            } else if (eventType === "step") {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? {
                        ...m,
                        generated_sql: data.generated_sql || m.generated_sql,
                        steps: [
                          ...m.steps,
                          {
                            node: data.node,
                            status_message: data.status_message,
                            generated_sql: data.generated_sql,
                            execution_time_ms: data.execution_time_ms,
                            timestamp: new Date().toLocaleTimeString(),
                          },
                        ],
                      }
                    : m
                )
              );
            } else if (eventType === "final_result") {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? {
                        ...m,
                        content: data.insights || m.content,
                        chart_spec: data.chart_spec || m.chart_spec,
                        isError: data.is_terminal_error || false,
                      }
                    : m
                )
              );
            } else if (eventType === "done") {
              setMessages((prev) =>
                prev.map((m) => (m.id === assistantId ? { ...m, isStreaming: false } : m))
              );
            } else if (eventType === "error") {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? {
                        ...m,
                        content: `### ⚠️ System Error\n${data.error || "An unexpected error occurred."}`,
                        isStreaming: false,
                        isError: true,
                      }
                    : m
                )
              );
            }
          } catch (jsonErr) {
            console.error("Error parsing SSE JSON payload:", jsonErr, dataStr);
          }
        }
      }
    } catch (err: any) {
      console.error("Fetch streaming error:", err);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? {
                ...m,
                content: `### ⚠️ Connection Error\nCould not reach backend API at ${API_BASE}. Make sure the FastAPI backend is running.\n\n*Error details: ${err.message}*`,
                isStreaming: false,
                isError: true,
              }
            : m
        )
      );
    } finally {
      setIsLoading(false);
      setMessages((prev) =>
        prev.map((m) => (m.id === assistantId ? { ...m, isStreaming: false } : m))
      );
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  return {
    messages,
    isLoading,
    sendMessage,
    clearChat,
  };
}
