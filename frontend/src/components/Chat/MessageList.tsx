import type { ChatMessage } from "@shared/types";

import { MessageBubble } from "./MessageBubble";

type MessageListProps = {
  messages: ChatMessage[];
  onFollowUpClick?: (question: string) => void;
};

export const MessageList = ({ messages, onFollowUpClick }: MessageListProps) => {
  // Filter out empty assistant messages (shown via TypingIndicator)
  // and any legacy review-system messages.
  const visibleMessages = messages.filter(
    (message) =>
      (message.role !== "assistant" || message.content.trim()) &&
      !message.content.startsWith("[REVIEW_REQUIRED]")
  );

  return (
    <div className="space-y-4">
      {visibleMessages.map((message) => (
        <MessageBubble key={message.id} message={message} onFollowUpClick={onFollowUpClick} />
      ))}
    </div>
  );
};

