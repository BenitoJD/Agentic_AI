import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypePrism from "rehype-prism-plus";
import { Copy, AlertTriangle, Info } from "lucide-react";
import { useState } from "react";

import type { ChatMessage } from "@shared/types";
import { BottleneckDisplay } from "../BottleneckDisplay";
import { KPIEditModal } from "../KPIEditModal";

type MessageBubbleProps = {
  message: ChatMessage;
  animate?: boolean;
  onFollowUpClick?: (question: string) => void;
};

export const MessageBubble = ({ message, animate = true }: MessageBubbleProps) => {
  const isUser = message.role === "user";
  const hasFollowUps = !!message.followUpQuestions?.length;
  const lowConfidence =
    typeof message.confidence === "number" && message.confidence < 0.5;
  const hasSources = Array.isArray(message.sources) && message.sources.length > 0;
  const hasWebSource = hasSources && message.sources!.some((source) => source.startsWith("http"));
  const modeLabel = isUser
    ? ""
    : hasWebSource
    ? "Mode: Web"
    : hasSources
    ? "Mode: Docs"
    : "Mode: Direct";
  const [showKPIModal, setShowKPIModal] = useState(false);
  
  // Show explain button for assistant messages (especially performance analysis)
  const showExplainButton = !isUser && (hasSources || message.bottlenecks?.length);

  return (
    <motion.div
      layout
      initial={animate ? { opacity: 0, y: 12 } : false}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18 }}
      className="flex w-full"
    >
      <div
        className={`${isUser ? "max-w-[75%]" : "max-w-[95%] md:max-w-[92%]"} rounded-xl px-4 py-2.5 text-sm md:text-base ${
          isUser
            ? "ml-auto bg-bubbleUser text-white"
            : "mr-auto bg-bubbleAssistant text-textPrimary"
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-line">{message.content}</p>
        ) : (
          <>
            {modeLabel && (
              <div className="mb-1">
                <span className="inline-flex items-center rounded-full border border-borderDark/70 bg-surfaceMuted px-2 py-0.5 text-[10px] text-textSecondary">
                  {modeLabel}
                </span>
              </div>
            )}

            <Markdown content={message.content || "…"} />

            {message.bottlenecks && message.bottlenecks.length > 0 && (
              <BottleneckDisplay bottlenecks={message.bottlenecks} />
            )}

            {hasSources && (
              <div className="mt-3 border-t border-borderDark/50 pt-2">
                <div className="flex items-center justify-between mb-1">
                  <p className="text-[11px] font-medium text-textSecondary">Sources</p>
                  {showExplainButton && (
                    <button
                      onClick={() => setShowKPIModal(true)}
                      className="inline-flex items-center gap-1 text-[11px] text-blue-400 hover:text-blue-300 transition-colors"
                    >
                      <Info className="h-3 w-3" />
                      Explain KPIs
                    </button>
                  )}
                </div>
                <ul className="space-y-0.5 text-[11px] text-textSecondary">
                  {message.sources.map((source) => (
                    <li key={source} className="truncate">
                      {source.startsWith("http") ? (
                        <a
                          href={source}
                          target="_blank"
                          rel="noreferrer"
                          className="underline underline-offset-2 hover:text-textPrimary"
                        >
                          {source}
                        </a>
                      ) : (
                        source
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {showExplainButton && !hasSources && (
              <div className="mt-3 border-t border-borderDark/50 pt-2">
                <button
                  onClick={() => setShowKPIModal(true)}
                  className="inline-flex items-center gap-1 text-[11px] text-blue-400 hover:text-blue-300 transition-colors"
                >
                  <Info className="h-3 w-3" />
                  Explain KPIs
                </button>
              </div>
            )}

            {showKPIModal && (
              <KPIEditModal
                isOpen={showKPIModal}
                onClose={() => setShowKPIModal(false)}
                onSave={() => {
                  // Optionally refresh or notify parent
                }}
              />
            )}

            {hasFollowUps && (
              <div className="mt-3 border-t border-borderDark/50 pt-2 text-[11px] text-textSecondary">
                <p className="mb-1 font-medium">To help me answer better, you could clarify:</p>
                <ul className="list-disc space-y-0.5 pl-4">
                  {message.followUpQuestions?.map((question) => (
                    <li key={question}>{question}</li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}
      </div>
    </motion.div>
  );
};

const Markdown = ({ content }: { content: string }) => {
  return (
    <ReactMarkdown
      className="prose max-w-none break-words text-black prose-headings:text-black prose-p:text-black prose-strong:text-black prose-em:text-black"
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[rehypePrism]}
      components={{
        code({ inline, className, children, ...props }) {
          const [copied, setCopied] = useState(false);
          const text = String(children).replace(/\n$/, "");
          const language = /language-(\w+)/.exec(className || "")?.[1] ?? "";

          if (inline) {
            return (
              <code className="rounded bg-white/10 px-1.5 py-0.5 text-sm text-white" {...props}>
                {children}
              </code>
            );
          }

          return (
            <div className="not-prose relative my-4">
              <button
                type="button"
                className="absolute right-3 top-3 inline-flex items-center gap-1 rounded-full bg-white/10 px-3 py-1 text-xs text-white hover:bg-white/20"
                onClick={() => {
                  navigator.clipboard.writeText(text);
                  setCopied(true);
                  setTimeout(() => setCopied(false), 1500);
                }}
              >
                <Copy className="h-3 w-3" /> {copied ? "Copied" : "Copy"}
              </button>
              <pre className="overflow-x-auto rounded-2xl bg-[#0b0b0f] p-4 text-sm text-white">
                <code className={`language-${language}`} {...props}>
                  {text}
                </code>
              </pre>
            </div>
          );
        },
      }}
    >
      {content}
    </ReactMarkdown>
  );
};

