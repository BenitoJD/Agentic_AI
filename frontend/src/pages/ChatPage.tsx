import { useEffect, useRef, useState } from "react";

import { ChatInput } from "../components/Chat/ChatInput";
import { MessageList } from "../components/Chat/MessageList";
import { TypingIndicator } from "../components/Chat/TypingIndicator";
import { Sidebar } from "../components/Sidebar/Sidebar";
import { Header } from "../components/Layout/Header";
import { PageLayout } from "../components/Layout/PageLayout";
import { useChat } from "../hooks/useChat";
import { useSidebar } from "../hooks/useSidebar";

type ChatPageProps = {
  onOpenUploads?: () => void;
};

export const ChatPage = ({ onOpenUploads }: ChatPageProps) => {
  const {
    threads,
    activeThreadId,
    messages,
    sendMessage,
    createNewThread,
    selectThread,
    deleteThread,
    isStreaming,
    isTyping,
    error,
  } = useChat();
  const { isMobileOpen, open, close } = useSidebar();
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [lockScroll, setLockScroll] = useState(false);

  useEffect(() => {
    const container = scrollRef.current;
    if (!container) return;

    const onScroll = () => {
      const nearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 80;
      setLockScroll(!nearBottom);
    };

    container.addEventListener("scroll", onScroll, { passive: true });
    return () => container.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    if (lockScroll) return;
    const container = scrollRef.current;
    if (!container) return;
    container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
  }, [messages, isTyping, lockScroll]);

  // Only show typing indicator if we're typing AND the last assistant message is empty (not streaming tokens yet)
  const lastMessage = messages[messages.length - 1];
  const showTyping = isTyping && (lastMessage?.role !== "assistant" || !lastMessage?.content.trim());

  return (
    <PageLayout>
      {isMobileOpen && (
        <Sidebar
          threads={threads}
          activeThreadId={activeThreadId}
          onNewChat={() => {
            createNewThread();
            close();
          }}
          onSelect={(id) => {
            selectThread(id);
            close();
          }}
          onDelete={(id) => {
            deleteThread(id);
            close();
          }}
          variant="mobile"
          onClose={close}
          onOpenUploads={onOpenUploads}
        />
      )}

      <div className="flex flex-1 flex-col">
        <Header onMenuClick={open} onUploadsClick={onOpenUploads} subtitle={error ?? undefined} />
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-10 sm:px-10">
          <div className="mx-auto flex w-full max-w-3xl flex-col">
            {messages.length === 0 && (
              <div className="mb-8 rounded-lg border border-borderDark bg-surfaceMuted px-4 py-3 text-sm text-textSecondary">
                <p className="mb-2 font-medium text-textPrimary">Performance Bottleneck Analyzer</p>
                <ul className="list-disc space-y-1 pl-5">
                  <li>Upload log files (.log, .txt) or metrics files (JSON, CSV) to analyze performance bottlenecks.</li>
                  <li>Ask questions like "What bottlenecks do you see?" or "Analyze the performance issues".</li>
                  <li>The AI will identify CPU, memory, network, database, and disk I/O bottlenecks.</li>
                  <li>Get actionable recommendations to resolve performance issues.</li>
                </ul>
              </div>
            )}

            <MessageList messages={messages} onFollowUpClick={sendMessage} />
          {showTyping && (
            <div className="mt-6">
              <TypingIndicator />
            </div>
          )}
          </div>
        </div>

        <div className="border-t border-borderDark px-4 py-5">
          <div className="mx-auto w-full max-w-3xl">
          {error && <p className="mb-3 text-sm text-red-400">{error}</p>}
          <ChatInput onSend={sendMessage} disabled={isStreaming} />
          </div>
        </div>
      </div>
    </PageLayout>
  );
};

