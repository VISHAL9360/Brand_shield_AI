import React from "react";
import { Sun, Moon } from "lucide-react";
import { useTheme } from "@/context/ThemeContext";

interface ThemeToggleProps {
  className?: string;
  showLabel?: boolean;
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({ className = "", showLabel = false }) => {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      type="button"
      id="theme-toggle-btn"
      onClick={toggleTheme}
      aria-label="Toggle color theme"
      title={isDark ? "Switch to Stripe Executive Daylight" : "Switch to Obsidian Dark Mode"}
      className={`relative inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all duration-200 cursor-pointer ${
        isDark
          ? "bg-[#181B26] border-[#1E293B] text-slate-200 hover:bg-[#202534] hover:text-white"
          : "bg-white border-[#E2E8F0] text-slate-700 hover:bg-slate-50 hover:text-slate-900 shadow-xs"
      } ${className}`}
    >
      <div className="relative w-4 h-4 flex items-center justify-center">
        {isDark ? (
          <Sun className="w-3.5 h-3.5 text-amber-400 animate-in fade-in zoom-in-75 duration-200" />
        ) : (
          <Moon className="w-3.5 h-3.5 text-indigo-600 animate-in fade-in zoom-in-75 duration-200" />
        )}
      </div>
      {showLabel && (
        <span className="tracking-tight">
          {isDark ? "Obsidian Dark" : "Executive Daylight"}
        </span>
      )}
    </button>
  );
};

export default ThemeToggle;
