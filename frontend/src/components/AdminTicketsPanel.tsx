import { useState } from "react";
import type { SupportTicket } from "../types";

function AdminTicketsPanel() {
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [isLoadingTickets, setIsLoadingTickets] = useState(false);
  const [ticketErrorMessage, setTicketErrorMessage] = useState("");

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

  async function resolveTicket(ticketId: string) {
    setTicketErrorMessage("");

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/tickets/${ticketId}/status?status=resolved`,
        {
          method: "PATCH",
        }
      );

      if (!response.ok) {
        throw new Error("Failed to update ticket status");
      }

      await fetchTickets();
    } catch (error) {
      setTicketErrorMessage("Failed to update ticket status.");
    }
  }

  return (
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
              <th>Action</th>
            </tr>
          </thead>

          <tbody>
            {tickets.map((ticket) => (
              <tr key={ticket.ticket_id}>
                <td>{ticket.ticket_id}</td>
                <td>{ticket.issue_type}</td>
                <td>{ticket.status}</td>
                <td>{ticket.summary}</td>
                <td>
                  {ticket.status !== "resolved" ? (
                    <button onClick={() => resolveTicket(ticket.ticket_id)}>
                      Mark Resolved
                    </button>
                  ) : (
                    <span>Resolved</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

export default AdminTicketsPanel;