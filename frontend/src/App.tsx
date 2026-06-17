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
};

function App() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

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
      };

      setMessages((previousMessages) => [...previousMessages, agentMessage]);
    } catch (error) {
      setErrorMessage("Failed to connect to the backend.");
    } finally {
      setIsLoading(false);
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
              <p className="tool-notice">
              Tool used: {chatMessage.toolUsed}
              </p>
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
    </main>
  );
}

export default App;