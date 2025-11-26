import { useCallback, useMemo, useState, useEffect } from "react";

import type { ChatMessage, ChatResponse } from "@shared/types";

export type ChatThread = {
  id: string;
  title: string;
  updatedAt: number;
  messages: ChatMessage[];
};

const STORAGE_KEY = "nova.chat.threads";

const createThread = (title = "New Chat"): ChatThread => ({
  id: crypto.randomUUID(),
  title,
  updatedAt: Date.now(),
  messages: [],
});

const sortByRecency = (items: ChatThread[]) => [...items].sort((a, b) => b.updatedAt - a.updatedAt);

const loadThreads = (): ChatThread[] => {
  if (typeof window === "undefined") return [createThread()];
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (!stored) return [createThread()];
    const parsed = JSON.parse(stored) as ChatThread[];
    if (!parsed.length) return [createThread()];

    // Clean up any old review-required system messages from previous builds.
    const cleaned = parsed.map((thread) => ({
      ...thread,
      messages: thread.messages.filter(
        (m) => !m.content.startsWith("[REVIEW_REQUIRED]")
      ),
    }));

    return cleaned.length ? cleaned : [createThread()];
  } catch {
    return [createThread()];
  }
};

export const useChat = () => {
  const initialThreads = useMemo(() => loadThreads(), []);
  const fallbackThread = initialThreads[0] ?? createThread();
  const [threads, setThreads] = useState<ChatThread[]>(initialThreads.length ? initialThreads : [fallbackThread]);
  const [activeThreadId, setActiveThreadId] = useState<string>(fallbackThread.id);
  const [isStreaming, setStreaming] = useState(false);
  const [isTyping, setTyping] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activeThread = useMemo(
    () => threads.find((thread) => thread.id === activeThreadId) ?? threads[0],
    [threads, activeThreadId]
  );

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(threads));
  }, [threads]);

  const mutateThread = useCallback((threadId: string, updater: (thread: ChatThread) => ChatThread) => {
    setThreads((prev) => {
      let updated = false;
      const mapped = prev.map((thread) => {
        if (thread.id === threadId) {
          updated = true;
          return updater(thread);
        }
        return thread;
      });
      return updated ? sortByRecency(mapped) : prev;
    });
  }, []);

  const ensureThread = useCallback(() => {
    if (activeThreadId && threads.some((thread) => thread.id === activeThreadId)) {
      return activeThreadId;
    }
    const fallback = createThread();
    setThreads((prev) => sortByRecency([fallback, ...prev]));
    setActiveThreadId(fallback.id);
    return fallback.id;
  }, [activeThreadId, threads]);

  const sendMessage = useCallback(
    async (rawText: string) => {
      const text = rawText.trim();
      if (!text) return;

      setError(null);

      let threadId = ensureThread();
      const existing = threads.find((thread) => thread.id === threadId);
      if (!existing) {
        const seeded = createThread(text.slice(0, 60) || "New Chat");
        setThreads((prev) => sortByRecency([seeded, ...prev]));
        threadId = seeded.id;
        setActiveThreadId(seeded.id);
      }

      const assistantId = crypto.randomUUID();
      const userMessage: ChatMessage = { id: crypto.randomUUID(), role: "user", content: text };
      const skeletonMessage: ChatMessage = { id: assistantId, role: "assistant", content: "" };

      mutateThread(threadId, (thread) => {
        const title = thread.messages.length === 0 ? text.slice(0, 60) || "New Chat" : thread.title;
        return {
          ...thread,
          title,
          updatedAt: Date.now(),
          messages: [...thread.messages, userMessage, skeletonMessage],
        };
      });

      const historyPayload =
        existing?.messages.map(({ role, content }) => ({
          role,
          content,
        })) ?? [];

      const lastAssistantWithSources = existing?.messages
        .filter((m) => m.role === "assistant" && Array.isArray(m.sources) && m.sources.length > 0)
        .at(-1);

      setStreaming(true);
      setTyping(true);

      try {
        const response = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: text,
            history: historyPayload,
            stream: false,
            metadata: {
              lastSources: lastAssistantWithSources?.sources ?? [],
            },
          }),
        });
        if (!response.ok) {
          throw new Error(await response.text());
        }
        const data = (await response.json()) as ChatResponse;
        mutateThread(threadId, (thread) => ({
          ...thread,
          updatedAt: Date.now(),
          messages: thread.messages.map((msg) =>
            msg.id === assistantId
              ? {
                  ...msg,
                  content: data.response,
                  sources: data.sources,
                  confidence: data.confidence,
                  followUpQuestions: data.followUpQuestions,
                }
              : msg
          ),
        }));
      } catch (err) {
        console.error("[chat] request failed", err);
        setError("Something went wrong. Please try again.");
        mutateThread(threadId, (thread) => ({
          ...thread,
          messages: thread.messages.map((msg) =>
            msg.id === assistantId ? { ...msg, content: "I ran into an error. Please try again." } : msg
          ),
        }));
      } finally {
        setTyping(false);
        setStreaming(false);
      }
    },
    [ensureThread, mutateThread, threads]
  );

  const createNewThread = useCallback(() => {
    const thread = createThread();
    setThreads((prev) => sortByRecency([thread, ...prev]));
    setActiveThreadId(thread.id);
    setTyping(false);
    setStreaming(false);
  }, []);

  const selectThread = useCallback((threadId: string) => {
    setActiveThreadId(threadId);
    setTyping(false);
    setStreaming(false);
  }, []);

  const deleteThread = useCallback(
    (threadId: string) => {
      setThreads((prev) => {
        const filtered = prev.filter((thread) => thread.id !== threadId);
        if (filtered.length === 0) {
          const newThread = createThread();
          setActiveThreadId(newThread.id);
          return [newThread];
        }
        if (activeThreadId === threadId) {
          const nextThread = filtered[0];
          setActiveThreadId(nextThread.id);
        }
        return sortByRecency(filtered);
      });
      setTyping(false);
      setStreaming(false);
    },
    [activeThreadId]
  );

  return {
    threads,
    activeThreadId,
    messages: activeThread?.messages ?? [],
    isStreaming,
    isTyping,
    error,
    sendMessage,
    createNewThread,
    selectThread,
    deleteThread,
  };
};

