export const TypingIndicator = () => (
  <div className="inline-flex items-center gap-2 rounded-full border border-borderDark bg-bubbleAssistant/80 px-4 py-2 text-sm text-textSecondary">
    <span className="flex gap-1">
      <span className="h-2 w-2 animate-bounce rounded-full bg-textSecondary [animation-delay:-0.2s]" />
      <span className="h-2 w-2 animate-bounce rounded-full bg-textSecondary [animation-delay:-0.1s]" />
      <span className="h-2 w-2 animate-bounce rounded-full bg-textSecondary" />
    </span>
    Nova is thinking…
  </div>
);

