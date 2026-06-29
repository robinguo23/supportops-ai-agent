import { useState } from "react";
import "./App.css";

type ChatResponse = {
  reply: string;
  needs_human_handoff: boolean;
  tool_used?: string | null;
  tool_result?: Record<string, unknown> | null;
};

type ChatMessage = {
  role: "user" | "agent";
  content: string;
  needsHumanHandoff?: boolean;
  toolUsed?: string | null;
  ticketId?: string | null;
};

type SupportTicket = {
  ticket_id: string;
  issue_type: string;
  summary: string;
  status: string;
  created_at: string;
};

function App() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingTickets, setIsLoadingTickets] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [ticketErrorMessage, setTicketErrorMessage] = useState("");

  async function sendMessage() {
    const trimmedMessage = message.trim();

    if (!trimmedMessage) {
      return;
    }

    const userMessage: ChatMessage = {
      role: "user",
      content: trimmedMessage,
    };

    setMessages((previousMessages) => [...previousMessages, userMessage]);
    setMessage("");
    setIsLoading(true);
    setErrorMessage("");

    try {
      const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: trimmedMessage,
        }),
      });

      if (!response.ok) {
        throw new Error("Backend request failed");
      }

      const data: ChatResponse = await response.json();

      const agentMessage: ChatMessage = {
        role: "agent",
        content: data.reply,
        needsHumanHandoff: data.needs_human_handoff,
        toolUsed: data.tool_used,
        ticketId:
          data.tool_result && "ticket_id" in data.tool_result
            ? String(data.tool_result.ticket_id)
            : null,
      };

      setMessages((previousMessages) => [...previousMessages, agentMessage]);
    } catch (error) {
      setErrorMessage("Failed to connect to the backend.");
    } finally {
      setIsLoading(false);
    }
  }

  async function fetchTickets() {
    setIsLoadingTickets(true);
    setTicketErrorMessage("");

    try {
      const response = await fetch("http://127.0.0.1:8000/tickets");

      if (!response.ok) {
        throw new Error("Failed to fetch tickets");
      }

      const data: { tickets: SupportTicket[] } = await response.json();
      setTickets(data.tickets);
    } catch (error) {
      setTicketErrorMessage("Failed to load support tickets.");
    } finally {
      setIsLoadingTickets(false);
    }
  }

  return (
    <main className="container">
      <h1>SupportOps AI Agent</h1>

      <p>Minimal chat interface connected to the FastAPI backend.</p>

      <section className="chat-window">
        {messages.length === 0 && (
          <p className="empty-state">No messages yet. Ask a support question.</p>
        )}

        {messages.map((chatMessage, index) => (
          <div key={index} className={`message ${chatMessage.role}`}>
            <strong>{chatMessage.role === "user" ? "User" : "Agent"}</strong>
            <p>{chatMessage.content}</p>

            {chatMessage.needsHumanHandoff && (
              <p className="handoff-notice">
                This conversation may need human support.
              </p>
            )}

            {chatMessage.toolUsed && (
              <p className="tool-notice">Tool used: {chatMessage.toolUsed}</p>
            )}

            {chatMessage.ticketId && (
              <p className="ticket-notice">Ticket ID: {chatMessage.ticketId}</p>
            )}
          </div>
        ))}
      </section>

      <textarea
        value={message}
        onChange={(event) => setMessage(event.target.value)}
        placeholder="Ask a customer support question..."
        rows={4}
      />

      <button onClick={sendMessage} disabled={isLoading}>
        {isLoading ? "Sending..." : "Send"}
      </button>

      {errorMessage && (
        <section className="error-box">
          <p>{errorMessage}</p>
        </section>
      )}

      <section className="admin-panel">
        <div className="admin-header">
          <h2>Admin Tickets</h2>
          <button onClick={fetchTickets} disabled={isLoadingTickets}>
            {isLoadingTickets ? "Loading..." : "Refresh Tickets"}
          </button>
        </div>

        {ticketErrorMessage && (
          <section className="error-box">
            <p>{ticketErrorMessage}</p>
          </section>
        )}

        {tickets.length === 0 && (
          <p className="empty-state">No tickets loaded yet.</p>
        )}

        {tickets.length > 0 && (
          <table className="tickets-table">
            <thead>
              <tr>
                <th>Ticket ID</th>
                <th>Issue Type</th>
                <th>Status</th>
                <th>Summary</th>
              </tr>
            </thead>
            <tbody>
              {tickets.map((ticket) => (
                <tr key={ticket.ticket_id}>
                  <td>{ticket.ticket_id}</td>
                  <td>{ticket.issue_type}</td>
                  <td>{ticket.status}</td>
                  <td>{ticket.summary}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </main>
  );
}

export default App;