export type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  sources?: string[];
  confidence?: number;
  followUpQuestions?: string[];
};

export type ChatResponse = {
  response: string;
  sources: string[];
  confidence?: number;
  confidenceLevel?: "low" | "medium" | "high";
  followUpQuestions?: string[];
};

export type StreamDelta =
  | { event: "status"; payload: { stage: string } }
  | { event: "trace"; payload: { type: "sources"; items: string[] } }
  | { event: "token"; payload: { text: string } }
  | { event: "final"; payload: { response: string; sources: string[] } };

