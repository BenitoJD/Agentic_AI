export interface ReviewStatus {
  review_id: string;
  agent_name: string;
  prompt: string;
  initial_response: string;
  confidence: number;
  context?: string;
  sources: string[];
  status: "pending" | "approved" | "rejected" | "modified";
  feedback?: string;
  modified_response?: string;
  created_at: string;
  updated_at?: string;
  thread_id?: string;
}

export interface ReviewResponse {
  approved: boolean;
  feedback?: string;
  modified_response?: string;
}

