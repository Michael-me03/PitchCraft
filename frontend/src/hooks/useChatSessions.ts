// ============================================================================
// SECTION: Imports
// ============================================================================

import { useState, useEffect, useCallback } from "react";
import type { ChatMessage, ChatSession, SessionSettings } from "../types/chat";

// ============================================================================
// SECTION: Constants
// ============================================================================

const STORAGE_KEY = "pitchcraft_sessions";
const ACTIVE_KEY = "pitchcraft_active_session";
const MAX_SESSIONS = 50;

// ============================================================================
// SECTION: Helpers
// ============================================================================

function generateId(): string {
  return crypto.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function loadSessions(): ChatSession[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function loadActiveId(): string | null {
  try {
    return localStorage.getItem(ACTIVE_KEY) || null;
  } catch {
    return null;
  }
}

const DEFAULT_SETTINGS: SessionSettings = {
  templateId: null,
  templateName: null,
  purpose: "business",
  language: "de",
};

// ============================================================================
// SECTION: Hook
// ============================================================================

export function useChatSessions() {
  const [sessions, setSessions] = useState<ChatSession[]>(loadSessions);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(loadActiveId);

  // ── Persistence ──────────────────────────────────────────────────────────
  useEffect(() => {
    try {
      // Strip to max sessions (keep most recent)
      const trimmed = sessions
        .sort((a, b) => b.updatedAt - a.updatedAt)
        .slice(0, MAX_SESSIONS);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
    } catch {
      // localStorage full — silently fail
    }
  }, [sessions]);

  useEffect(() => {
    try {
      if (activeSessionId) {
        localStorage.setItem(ACTIVE_KEY, activeSessionId);
      } else {
        localStorage.removeItem(ACTIVE_KEY);
      }
    } catch {
      // silently fail
    }
  }, [activeSessionId]);

  // ── Computed ─────────────────────────────────────────────────────────────
  const activeSession = sessions.find((s) => s.id === activeSessionId) ?? null;

  // ── Actions ──────────────────────────────────────────────────────────────
  const createSession = useCallback((): string => {
    const id = generateId();
    const session: ChatSession = {
      id,
      title: "New Chat",
      createdAt: Date.now(),
      updatedAt: Date.now(),
      messages: [],
      settings: { ...DEFAULT_SETTINGS },
    };
    setSessions((prev) => [session, ...prev]);
    setActiveSessionId(id);
    return id;
  }, []);

  const addMessage = useCallback((sessionId: string, message: ChatMessage) => {
    setSessions((prev) =>
      prev.map((s) => {
        if (s.id !== sessionId) return s;
        const updated = {
          ...s,
          messages: [...s.messages, message],
          updatedAt: Date.now(),
        };
        // Auto-title from first user message
        if (
          s.title === "New Chat" &&
          message.role === "user" &&
          message.content.trim()
        ) {
          updated.title = message.content.trim().slice(0, 50);
        }
        return updated;
      }),
    );
  }, []);

  const updateSession = useCallback(
    (sessionId: string, updates: Partial<ChatSession>) => {
      setSessions((prev) =>
        prev.map((s) =>
          s.id === sessionId ? { ...s, ...updates, updatedAt: Date.now() } : s,
        ),
      );
    },
    [],
  );

  const updateSettings = useCallback(
    (sessionId: string, settings: Partial<SessionSettings>) => {
      setSessions((prev) =>
        prev.map((s) =>
          s.id === sessionId
            ? {
                ...s,
                settings: { ...s.settings, ...settings },
                updatedAt: Date.now(),
              }
            : s,
        ),
      );
    },
    [],
  );

  const deleteSession = useCallback(
    (sessionId: string) => {
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (activeSessionId === sessionId) {
        setActiveSessionId(null);
      }
    },
    [activeSessionId],
  );

  const renameSession = useCallback(
    (sessionId: string, title: string) => {
      setSessions((prev) =>
        prev.map((s) =>
          s.id === sessionId ? { ...s, title, updatedAt: Date.now() } : s,
        ),
      );
    },
    [],
  );

  return {
    sessions,
    activeSession,
    activeSessionId,
    setActiveSessionId,
    createSession,
    addMessage,
    updateSession,
    updateSettings,
    deleteSession,
    renameSession,
  };
}
