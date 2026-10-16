import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Olist Autonomous BI Agent | Multi-Agent Analytics",
  description:
    "Enterprise-grade Business Intelligence system driven by a LangGraph 4-agent pod, DuckDB in-memory OLAP engine, and dynamic Recharts visualizations.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#070b14] text-slate-100 antialiased selection:bg-blue-600 selection:text-white">
        {children}
      </body>
    </html>
  );
}
