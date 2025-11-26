import { Trash2 } from "lucide-react";
import clsx from "clsx";

import type { ChatThread } from "../../hooks/useChat";

type ChatListItemProps = {
  thread: ChatThread;
  isActive: boolean;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
};

const formatTimestamp = (timestamp: number) => {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
};

export const ChatListItem = ({ thread, isActive, onSelect, onDelete }: ChatListItemProps) => {
  const handleDelete = (event: React.MouseEvent) => {
    event.stopPropagation();
    onDelete(thread.id);
  };

  return (
    <div
      className={clsx(
        "group relative flex w-full items-center gap-2 rounded-xl px-4 py-3 transition",
        isActive ? "bg-white/5 text-white shadow-[0_0_12px_rgba(0,0,0,0.35)]" : "text-textSecondary hover:bg-white/5"
      )}
    >
      <button
        type="button"
        onClick={() => onSelect(thread.id)}
        className="flex-1 text-left"
      >
        <p className="line-clamp-2 text-sm">{thread.title}</p>
        <p className="text-xs text-textSecondary">{formatTimestamp(thread.updatedAt)}</p>
      </button>
      <button
        type="button"
        onClick={handleDelete}
        className="opacity-0 transition-opacity group-hover:opacity-100 hover:text-red-400"
        title="Delete chat"
      >
        <Trash2 className="h-4 w-4" />
      </button>
    </div>
  );
};

