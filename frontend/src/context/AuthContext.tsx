import React, { createContext, useContext, useEffect, useState } from "react";
import brandshield, { User, UserRole } from "@/api/brandshieldClient";

export interface SeededCredential {
  role: UserRole;
  label: string;
  email: string;
  password: string;
  name: string;
  title: string;
  badgeClass: string;
  description: string;
}

export const SEEDED_CREDENTIALS: Record<UserRole, SeededCredential> = {
  ADMINISTRATOR: {
    role: "ADMINISTRATOR",
    label: "Administrator",
    email: "administrator@brandshield.ai",
    password: "DemoSecure2026!",
    name: "Elena Rostova",
    title: "Governance Lead & Workspace Admin",
    badgeClass: "badge-purple",
    description: "Full workspace sovereignty, policy engine configs, attestation key control, and audit ledger validation.",
  },
  CREATOR: {
    role: "CREATOR",
    label: "Creator",
    email: "creator@brandshield.ai",
    password: "DemoSecure2026!",
    name: "Alex Chen",
    title: "Product Marketing Lead",
    badgeClass: "badge-emerald",
    description: "Ingests multi-modal copy, inspects real-time preflight highlights, and accepts/rejects AI remediation suggestions.",
  },
  REVIEWER: {
    role: "REVIEWER",
    label: "Reviewer",
    email: "reviewer@brandshield.ai",
    password: "DemoSecure2026!",
    name: "Marcus Vance",
    title: "Legal & Regulatory Counsel",
    badgeClass: "badge-amber",
    description: "Evaluates ungrounded assertions, inspects character-level diffs, and signs cryptographic approval attestations.",
  },
};

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<User>;
  logout: () => void;
  clearError: () => void;
}

const TOKEN_KEY = "brandshield_access_token";
const USER_KEY = "brandshield_user_profile";

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setTokenState] = useState<string | null>(() => {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  });

  const [user, setUserState] = useState<User | null>(() => {
    try {
      const raw = localStorage.getItem(USER_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  });

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Initialize client with stored token
  useEffect(() => {
    if (token) {
      brandshield.setToken(token);
      if (user?.role) {
        brandshield.setActiveDemoRole(user.role);
      }
    }
    setIsLoading(false);
  }, [token, user]);

  const login = async (email: string, password: string): Promise<User> => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await brandshield.login(email, password);
      const loggedUser = res.user;
      const accessToken = res.access_token;

      setTokenState(accessToken);
      setUserState(loggedUser);

      try {
        localStorage.setItem(TOKEN_KEY, accessToken);
        localStorage.setItem(USER_KEY, JSON.stringify(loggedUser));
      } catch {
        // storage quota or incognito fallback
      }

      brandshield.setToken(accessToken);
      if (loggedUser.role) {
        brandshield.setActiveDemoRole(loggedUser.role);
      }

      return loggedUser;
    } catch (err: any) {
      const msg = err.message || "Authentication failed. Please verify credentials.";
      setError(msg);
      throw new Error(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setTokenState(null);
    setUserState(null);
    setError(null);
    try {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    } catch {
      // ignore
    }
    brandshield.setToken(null);
    brandshield.setActiveDemoRole(null);
  };

  const clearError = () => setError(null);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token && !!user,
        isLoading,
        error,
        login,
        logout,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
