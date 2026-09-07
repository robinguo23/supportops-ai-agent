import { useState } from "react";

import "./App.css";
import AdminTicketsPanel from "./components/AdminTicketsPanel";
import ChatPanel from "./components/ChatPanel";
import SecurityDashboard from "./components/SecurityDashboard";


type View = "chat" | "tickets" | "security";


function App() {
  const [view, setView] = useState<View>("chat");

  return (
    <main className="container">
      <header className="app-header">
        <h1>SupportOps AI Agent</h1>

        <nav className="app-nav" aria-label="Application sections">
          <button
            type="button"
            className={view === "chat" ? "active" : ""}
            onClick={() => setView("chat")}
          >
            Support Chat
          </button>

          <button
            type="button"
            className={view === "tickets" ? "active" : ""}
            onClick={() => setView("tickets")}
          >
            Admin Tickets
          </button>

          <button
            type="button"
            className={view === "security" ? "active" : ""}
            onClick={() => setView("security")}
          >
            Security
          </button>
        </nav>
      </header>

      {view === "chat" && <ChatPanel />}
      {view === "tickets" && <AdminTicketsPanel />}
      {view === "security" && <SecurityDashboard />}
    </main>
  );
}

export default App;
