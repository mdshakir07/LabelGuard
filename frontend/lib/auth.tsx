"use client";

import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useSyncExternalStore,
} from "react";
import { clearAuth, getUser, setUser as storeUser } from "./api";
import { User } from "./types";

interface AuthSnapshot {
  user: User | null;
  ready: boolean;
}

interface AuthContextValue extends AuthSnapshot {
  setUser: (u: User) => void;
  logout: () => void;
}

const SERVER_SNAPSHOT: AuthSnapshot = { user: null, ready: false };

let snapshot: AuthSnapshot = SERVER_SNAPSHOT;
const listeners = new Set<() => void>();

function notify() {
  listeners.forEach((l) => l());
}

function getSnapshot(): AuthSnapshot {
  if (!snapshot.ready && typeof window !== "undefined") {
    snapshot = { user: getUser(), ready: true };
  }
  return snapshot;
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  window.addEventListener("storage", onStorageEvent);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", onStorageEvent);
  };
}

function onStorageEvent(e: StorageEvent) {
  if (e.storageArea === window.localStorage) {
    snapshot = { user: getUser(), ready: true };
    notify();
  }
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const state = useSyncExternalStore(subscribe, getSnapshot, () => SERVER_SNAPSHOT);

  const setUser = useCallback((u: User) => {
    storeUser(u);
    snapshot = { user: u, ready: true };
    notify();
  }, []);

  const logout = useCallback(() => {
    clearAuth();
    snapshot = { user: null, ready: true };
    notify();
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, setUser, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}