import { useState } from "react";
import "./App.css";

type ChatResponse = {
  reply: string;
  needs_human_handoff: boolean;
};

function App() {
  const [message, setMessage] = useState("");
  const [reply, setReply] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  async function sendMessage() {
    if (!message.trim()) {
      return;
    }

    setIsLoading(true);
    setErrorMessage("");
    setReply("");

    try {
      const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: message,
        }),
      });

      if (!response.ok) {
        throw new Error("Backend request failed");
      }

      const data: ChatResponse = await response.json();
      setReply(data.reply);
    } catch (error) {
      setErrorMessage("Failed to connect to the backend.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="container">
      <h1>SupportOps AI Agent</h1>

      <p>
        Minimal frontend connected to the FastAPI backend.
      </p>

      <textarea
        value={message}
        onChange={(event) => setMessage(event.target.value)}
        placeholder="Ask a customer support question..."
        rows={4}
      />

      <button onClick={sendMessage} disabled={isLoading}>
        {isLoading ? "Sending..." : "Send"}
      </button>

      {reply && (
        <section className="response-box">
          <h2>Agent Reply</h2>
          <p>{reply}</p>
        </section>
      )}

      {errorMessage && (
        <section className="error-box">
          <p>{errorMessage}</p>
        </section>
      )}
    </main>
  );
}

export default App;