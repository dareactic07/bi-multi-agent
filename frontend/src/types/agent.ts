export type ChartType = "bar" | "line" | "area" | "pie" | "metric_card";

export interface ChartSpec {
  chart_type: ChartType;
  title: string;
  x_axis_key: string;
  y_axis_keys: string[];
  data: Record<string, any>[];
  summary?: string;
}

export interface QueryResult {
  columns: string[];
  rows: Record<string, any>[];
  row_count: number;
  execution_time_ms: number;
  sanitized_sql: string;
}

export interface AgentStep {
  node: string;
  status_message: string;
  generated_sql?: string;
  execution_time_ms?: number;
  timestamp: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  generated_sql?: string;
  query_result?: QueryResult;
  chart_spec?: ChartSpec;
  steps: AgentStep[];
  isStreaming?: boolean;
  isError?: boolean;
  timestamp: string;
}
