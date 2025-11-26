import { motion } from "framer-motion";
import { Plus } from "lucide-react";
import clsx from "clsx";

import type { ChatThread } from "../../hooks/useChat";
import { ChatListItem } from "./ChatListItem";

type SidebarProps = {
  threads: ChatThread[];
  activeThreadId: string;
  onNewChat: () => void;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  variant: "desktop" | "mobile";
  onClose?: () => void;
  onOpenUploads?: () => void;
};

export const Sidebar = ({
  threads,
  activeThreadId,
  onNewChat,
  onSelect,
  onDelete,
  variant,
  onClose,
  onOpenUploads,
}: SidebarProps) => {
  const content = (
    <div className="flex h-full flex-col bg-sidebar text-textPrimary">
      <div className="flex items-center justify-between px-4 pb-3 pt-4 border-b border-borderDark/60">
        <p className="text-sm font-medium text-textPrimary">Chats</p>
        <button
          type="button"
          onClick={onNewChat}
          className="inline-flex items-center gap-1.5 rounded-full border border-borderDark px-2.5 py-1 text-[11px] text-textPrimary hover:bg-white/5"
        >
          <Plus className="h-3 w-3" /> New
        </button>
      </div>

      <div className="flex-1 space-y-2 overflow-y-auto px-3 py-3">
        {threads.map((thread) => (
          <ChatListItem
            key={thread.id}
            thread={thread}
            isActive={thread.id === activeThreadId}
            onSelect={onSelect}
            onDelete={onDelete}
          />
        ))}
        {threads.length === 0 && (
          <div className="rounded-xl border border-dashed border-borderDark px-4 py-6 text-center text-sm text-textSecondary">
            No conversations yet
          </div>
        )}
      </div>

      <div className="border-t border-borderDark px-4 py-4">
        <p className="mb-2 text-xs font-medium text-textSecondary">Uploads</p>
        <button
          type="button"
          onClick={() => {
            onOpenUploads?.();
            onClose?.();
          }}
          className="text-xs text-textPrimary underline-offset-2 hover:underline"
        >
          Open uploads page
        </button>
      </div>
    </div>
  );

  if (variant === "mobile") {
    return (
      <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur" onClick={onClose}>
        <motion.div
          initial={{ x: -320 }}
          animate={{ x: 0 }}
          exit={{ x: -320 }}
          transition={{ type: "spring", stiffness: 260, damping: 30 }}
          className="h-full w-72"
          onClick={(event) => event.stopPropagation()}
        >
          {content}
        </motion.div>
      </div>
    );
  }

  return (
    <motion.aside
      layout
      className={clsx("hidden h-full w-[260px] flex-shrink-0 border-r border-borderDark md:block")}
    >
      {content}
    </motion.aside>
  );
};

