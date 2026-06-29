export type ChatResponse = {
  reply: string;
  needs_human_handoff: boolean;
  tool_used?: string | null;
  tool_result?: Record<string, unknown> | null;
};

export type ChatMessage = {
  role: "user" | "agent";
  content: string;
  needsHumanHandoff?: boolean;
  toolUsed?: string | null;
  ticketId?: string | null;
};

export type SupportTicket = {
  ticket_id: string;
  issue_type: string;
  summary: string;
  status: string;
  created_at: string;
};