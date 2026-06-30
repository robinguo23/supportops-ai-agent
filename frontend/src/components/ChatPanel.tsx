import { useState } from "react";

import { API_BASE_URL } from "../config/api";
import type { ChatMessage, ChatResponse } from "../types";


export default function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Hello! I am your support assistant. You can ask about orders, returns, refunds, delivery, or damaged items.",
    },
  ]);

  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleSendMessage() {
    const trimmedInput = input.trim();

    if (!trimmedInput || isLoading) {
      return;
    }

    const userMessage: ChatMessage = {
      role: "user",
      content: trimmedInput,
    };

    setMessages((currentMessages) => [...currentMessages, userMessage]);
    setInput("");
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: trimmedInput,
        }),
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const data: ChatResponse = await response.json();

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: data.reply,
        toolUsed: data.tool_used,
        toolResult: data.tool_result,
      };

      setMessages((currentMessages) => [
        ...currentMessages,
        assistantMessage,
      ]);
    } catch (error) {
      console.error(error);

      setErrorMessage(
        "Sorry, something went wrong while contacting the support assistant."
      );
    } finally {
      setIsLoading(false);
    }
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  }

  return (
    <section className="chat-panel">
      <h2>Support Chat</h2>

      <div className="chat-messages">
        {messages.map((message, index) => (
          <div
            key={`${message.role}-${index}`}
            className={`chat-message ${message.role}`}
          >
            <div className="message-role">
              {message.role === "user" ? "You" : "Assistant"}
            </div>

            <div className="message-content">{message.content}</div>

            {message.toolUsed && (
              <div className="tool-used">
                Tool used: {message.toolUsed}
              </div>
            )}

            {message.toolResult?.sources &&
              message.toolResult.sources.length > 0 && (
                <div className="sources">
                  <div className="sources-title">Sources</div>

                  {message.toolResult.sources.map((source, sourceIndex) => (
                    <div
                      key={`${source.source}-${sourceIndex}`}
                      className="source-item"
                    >
                      <div>
                        {source.title} · {source.source}
                      </div>

                      {typeof source.similarity === "number" && (
                        <div>
                          Similarity: {(source.similarity * 100).toFixed(1)}%
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
          </div>
        ))}

        {isLoading && (
          <div className="chat-message assistant">
            <div className="message-role">Assistant</div>
            <div className="message-content">Thinking...</div>
          </div>
        )}
      </div>

      {errorMessage && <div className="error-message">{errorMessage}</div>}

      <div className="chat-input-area">
        <textarea
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your order, return policy, refund time, or delivery..."
          rows={3}
        />

        <button
          type="button"
          onClick={handleSendMessage}
          disabled={isLoading || input.trim().length === 0}
        >
          {isLoading ? "Sending..." : "Send"}
        </button>
      </div>
    </section>
  );
}