import React, { useState, useEffect } from "react";
import { ThemeProvider } from "@/context/ThemeContext";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { PipelineProvider } from "@/context/PipelineContext";
import { Navbar } from "@/components/Navbar";
import { LoginPage } from "@/pages/LoginPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { PipelineWizardLayout } from "@/pages/PipelineWizardLayout";
import { Shield } from "lucide-react";

const AppContent: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [activeView, setActiveView] = useState<"wizard" | "telemetry">("wizard");
  const [currentPath, setCurrentPath] = useState<string>(() => {
    return window.location.hash ? window.location.hash.replace("#", "") : "/";
  });

  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace("#", "") || "/";
      setCurrentPath(hash);
      if (hash === "/telemetry" || hash === "/dashboard") {
        setActiveView("telemetry");
      } else if (hash === "/wizard" || hash === "/pipeline") {
        setActiveView("wizard");
      }
    };
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  // Synchronize route with authentication status
  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated) {
        if (currentPath !== "/login") {
          window.location.hash = "/login";
          setCurrentPath("/login");
        }
      } else {
        if (currentPath === "/login" || currentPath === "/") {
          window.location.hash = "/pipeline";
          setCurrentPath("/pipeline");
          setActiveView("wizard");
        }
      }
    }
  }, [isAuthenticated, isLoading, currentPath]);

  const handleViewChange = (view: "wizard" | "telemetry") => {
    setActiveView(view);
    window.location.hash = view === "wizard" ? "/pipeline" : "/telemetry";
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC] dark:bg-[#090A0F] text-slate-900 dark:text-white transition-colors">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-indigo-600 flex items-center justify-center text-white shadow-xl shadow-indigo-500/25 animate-pulse">
            <Shield className="w-6 h-6 stroke-[2.2]" />
          </div>
          <div className="text-xs font-mono font-medium text-slate-500 dark:text-slate-400">
            Initializing BrandShield Sovereign Perimeter...
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <LoginPage
        onSuccessLogin={() => {
          window.location.hash = "/pipeline";
          setCurrentPath("/pipeline");
          setActiveView("wizard");
        }}
      />
    );
  }

  return (
    <PipelineProvider>
      <div className="min-h-screen flex flex-col bg-[#F8FAFC] dark:bg-[#090A0F] text-slate-900 dark:text-slate-100 transition-colors duration-200">
        <Navbar
          activeView={activeView}
          onViewChange={handleViewChange}
          onLogout={() => {
            window.location.hash = "/login";
            setCurrentPath("/login");
          }}
        />
        <main className="flex-1 pb-16">
          {activeView === "wizard" ? (
            <PipelineWizardLayout />
          ) : (
            <DashboardPage />
          )}
        </main>
      </div>
    </PipelineProvider>
  );
};

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;
