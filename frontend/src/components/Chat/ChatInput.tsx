import { FormEvent, KeyboardEvent, useState } from "react";
import { SendHorizonal } from "lucide-react";

import { useAutoResize } from "../../hooks/useAutoResize";

type ChatInputProps = {
  onSend: (value: string) => Promise<void> | void;
  disabled?: boolean;
};

export const ChatInput = ({ onSend, disabled }: ChatInputProps) => {
  const [value, setValue] = useState("");
  const { ref, resize, reset } = useAutoResize(6);

  const handleSubmit = async (event?: FormEvent) => {
    event?.preventDefault();
    if (!value.trim() || disabled) return;
    await onSend(value);
    setValue("");
    reset();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void handleSubmit();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="rounded-xl border border-borderDark bg-surfaceMuted/80 p-2">
      <div className="flex items-center gap-2.5">
        <textarea
          ref={ref}
          className="max-h-48 min-h-[40px] flex-1 resize-none bg-transparent text-sm leading-5 text-textPrimary placeholder:text-textSecondary focus:outline-none py-2"
          placeholder="Message Nova…"
          value={value}
          disabled={disabled}
          onChange={(event) => {
            setValue(event.target.value);
            resize();
          }}
          onKeyDown={handleKeyDown}
        />
        <button
          type="submit"
          disabled={disabled || !value.trim()}
          className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-accent text-white transition hover:bg-accent/80 disabled:bg-borderDark disabled:opacity-50 flex-shrink-0"
        >
          <SendHorizonal className="h-4 w-4" />
        </button>
      </div>
    </form>
  );
};

