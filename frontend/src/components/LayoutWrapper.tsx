"use client";

import Navigation from "../components/Navigation";
import { useState, useEffect } from "react";

export default function LayoutWrapper({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Initialize from localStorage if available
  useEffect(() => {
    const saved = localStorage.getItem("sidebar-collapsed");
    if (saved) setIsCollapsed(saved === "true");
  }, []);

  const toggleCollapsed = (collapsed: boolean) => {
    setIsCollapsed(collapsed);
    localStorage.setItem("sidebar-collapsed", String(collapsed));
  };

  return (
    <body className="min-h-full flex bg-slate-950 overflow-hidden">
      <Navigation isCollapsed={isCollapsed} setIsCollapsed={toggleCollapsed} />
      <main className="flex-1 overflow-y-auto h-screen relative">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(37,99,235,0.05),transparent)] pointer-events-none"></div>
        {children}
      </main>
    </body>
  );
}
