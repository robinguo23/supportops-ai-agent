export type ToolSource = {
  document_id: string;
  title: string;
  source: string;
  similarity?: number;
};

export type ConversationAction =
  | "ask_resolution_feedback"
  | "ask_escalation"
  | "allow_new_question";

export type ChatResponse = {
  reply: string;
  needs_human_handoff: boolean;
  tool_used?: string | null;
  tool_result?: {
    matched_chunks?: unknown[];
    sources?: ToolSource[];
    min_similarity?: number;
    reason?: string;
    original_query?: string;
    conversation_action?: ConversationAction;
    [key: string]: unknown;
  } | null;
};

export type ChatMessageActionType =
  | "resolution_feedback"
  | "escalation";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  toolUsed?: string | null;
  toolResult?: ChatResponse["tool_result"];
  actionType?: ChatMessageActionType;
  isActionActive?: boolean;
};

export type SupportTicket = {
  ticket_id: string;
  issue_type: string;
  summary: string;
  status: string;
  created_at?: string;
};