import { useCallback, useLayoutEffect, useRef } from "react";

export const useAutoResize = (maxRows = 6) => {
  const ref = useRef<HTMLTextAreaElement | null>(null);

  const resize = useCallback(() => {
    const textarea = ref.current;
    if (!textarea) return;
    const lineHeight = parseInt(window.getComputedStyle(textarea).lineHeight || "24", 10);
    const maxHeight = lineHeight * maxRows;

    textarea.style.height = "auto";
    const height = Math.min(textarea.scrollHeight, maxHeight);
    textarea.style.height = `${height}px`;
    textarea.style.overflowY = textarea.scrollHeight > maxHeight ? "auto" : "hidden";
  }, [maxRows]);

  const reset = useCallback(() => {
    const textarea = ref.current;
    if (!textarea) return;
    textarea.style.height = "";
    textarea.style.overflowY = "hidden";
  }, []);

  useLayoutEffect(() => {
    resize();
  }, [resize]);

  return { ref, resize, reset };
};

