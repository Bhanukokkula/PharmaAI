import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api, setActiveUserId, type Persona, type User } from "./api";
import { useCart } from "./CartContext";

interface AuthContextValue {
  /** The active mock user (always set — guests browse as a default seeded user). */
  user: User | null;
  /** Whether the shopper has gone through the mock sign-in flow. */
  isSignedIn: boolean;
  /** Sample personas for "quick demo: shop as a sample customer". */
  personas: Persona[];
  /** Segment label for the active persona, when signed in via "shop as" — null otherwise. */
  segmentLabel: string | null;
  loading: boolean;
  signIn: (email: string) => Promise<void>;
  signInAsPersona: (userId: number) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

// Maps an email (any input — the password is ignored) to one of the first
// 200 seeded users, so "signing in" with different emails feels like
// different accounts without any real auth or persistence.
function emailToUserId(email: string): number {
  let hash = 0;
  for (let i = 0; i < email.length; i++) {
    hash = (hash * 31 + email.charCodeAt(i)) >>> 0;
  }
  return (hash % 200) + 1;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isSignedIn, setIsSignedIn] = useState(false);
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [segmentLabel, setSegmentLabel] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const { refresh: refreshCart } = useCart();

  useEffect(() => {
    api.listPersonas().then(setPersonas).catch(() => setPersonas([]));
    // Guests browse as the API's default seeded user (X-User-Id omitted) so
    // cart/recommendations work before signing in.
    api
      .getActiveUser()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  const signInAsPersona = useCallback(
    async (userId: number) => {
      setActiveUserId(userId);
      const activeUser = await api.getActiveUser();
      setUser(activeUser);
      setIsSignedIn(true);
      setSegmentLabel(personas.find((p) => p.id === userId)?.segment_label ?? null);
      await refreshCart();
    },
    [personas, refreshCart]
  );

  const signIn = useCallback(
    async (email: string) => {
      await signInAsPersona(emailToUserId(email));
    },
    [signInAsPersona]
  );

  const signOut = useCallback(async () => {
    setActiveUserId(null);
    setIsSignedIn(false);
    setSegmentLabel(null);
    try {
      setUser(await api.getActiveUser());
    } catch {
      setUser(null);
    }
    await refreshCart();
  }, [refreshCart]);

  return (
    <AuthContext.Provider
      value={{ user, isSignedIn, personas, segmentLabel, loading, signIn, signInAsPersona, signOut }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
