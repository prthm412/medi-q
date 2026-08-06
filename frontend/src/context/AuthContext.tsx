import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { login as apiLogin, signup as apiSignup } from "@/api/auth";
import type { UserRole } from "@/types";

interface DecodedToken {
  sub: string;
  role: UserRole;
  exp: number;
}

interface AuthUser {
  id: string;
  role: UserRole;
}

interface AuthContextValue {
  user: AuthUser | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, role: UserRole) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function decodeToken(token: string): AuthUser {
  const payload: DecodedToken = JSON.parse(atob(token.split(".")[1]));
  return { id: payload.sub, role: payload.role };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("mediqueue_token");
    if (token) {
      try {
        setUser(decodeToken(token));
      } catch {
        localStorage.removeItem("mediqueue_token");
      }
    }
    setLoading(false);
  }, []);

  async function login(email: string, password: string) {
    const token = await apiLogin(email, password);
    localStorage.setItem("mediqueue_token", token);
    setUser(decodeToken(token));
  }

  async function signup(email: string, password: string, role: UserRole) {
    await apiSignup(email, password, role);
    await login(email, password);
  }

  function logout() {
    localStorage.removeItem("mediqueue_token");
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, login, signup, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}