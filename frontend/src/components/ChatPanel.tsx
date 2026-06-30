import { useEffect, useState, type KeyboardEvent } from "react";

import { API_BASE_URL } from "../config/api";
import type {
  ChatMessage,
  ChatMessageActionType,
  ChatResponse,
} from "../types";


type PendingAction = {
  messageId: string;
  type: ChatMessageActionType;
  originalQuery: string;
};


const ACTION_TIMEOUT_MS = 2 * 60 * 1000;


function createMessageId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}


function getOriginalQuery(data: ChatResponse, fallback: string) {
  const originalQuery = data.tool_result?.original_query;

  if (typeof originalQuery === "string" && originalQuery.trim()) {
    return originalQuery;
  }

  return fallback;
}


function getActionType(data: ChatResponse): ChatMessageActionType | undefined {
  const action = data.tool_result?.conversation_action;

  if (action === "ask_resolution_feedback") {
    return "resolution_feedback";
  }

  if (action === "ask_escalation") {
    return "escalation";
  }

  return undefined;
}


export default function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: createMessageId(),
      role: "assistant",
      content:
        "Hello! I am your support assistant. You can ask about orders, returns, refunds, delivery, or damaged items.",
    },
  ]);

  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [pendingAction, setPendingAction] = useState<PendingAction | null>(
    null
  );

 const isInputLocked = pendingAction?.type === "escalation";

  useEffect(() => {
  if (!pendingAction || pendingAction.type !== "escalation") {
    return;
  }

    const timeoutId = window.setTimeout(() => {
      deactivateActionButtons(pendingAction.messageId);

      const timeoutMessage: ChatMessage = {
        id: createMessageId(),
        role: "assistant",
        content:
          "This conversation has timed out because no option was selected. You can start a new support question.",
      };

      setMessages((currentMessages) => [...currentMessages, timeoutMessage]);
      setPendingAction(null);
    }, ACTION_TIMEOUT_MS);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [pendingAction]);

  function deactivateActionButtons(messageId: string) {
    setMessages((currentMessages) =>
      currentMessages.map((message) =>
        message.id === messageId
          ? {
              ...message,
              isActionActive: false,
            }
          : message
      )
    );
  }

  function addAssistantMessage(message: Omit<ChatMessage, "id" | "role">) {
    const assistantMessage: ChatMessage = {
      id: createMessageId(),
      role: "assistant",
      ...message,
    };

    setMessages((currentMessages) => [
      ...currentMessages,
      assistantMessage,
    ]);

    return assistantMessage;
  }

  async function sendMessage(messageText: string) {
    const trimmedInput = messageText.trim();

    if (!trimmedInput || isLoading || isInputLocked) {
      return;
    }
    if (pendingAction?.type === "resolution_feedback") {
        deactivateActionButtons(pendingAction.messageId);
        setPendingAction(null);
    }

    const userMessage: ChatMessage = {
      id: createMessageId(),
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

      const actionType = getActionType(data);
      const assistantMessageId = createMessageId();

      const assistantMessage: ChatMessage = {
        id: assistantMessageId,
        role: "assistant",
        content: data.reply,
        toolUsed: data.tool_used,
        toolResult: data.tool_result,
        actionType,
        isActionActive: Boolean(actionType),
      };

      setMessages((currentMessages) => [
        ...currentMessages,
        assistantMessage,
      ]);

      if (actionType) {
        setPendingAction({
          messageId: assistantMessageId,
          type: actionType,
          originalQuery: getOriginalQuery(data, trimmedInput),
        });
      } else {
        setPendingAction(null);
      }
    } catch (error) {
      console.error(error);

      setErrorMessage(
        "Sorry, something went wrong while contacting the support assistant."
      );
    } finally {
      setIsLoading(false);
    }
  }

  function handleSendMessage() {
    void sendMessage(input);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  }

  function handleResolved(messageId: string) {
    deactivateActionButtons(messageId);
    setPendingAction(null);

    addAssistantMessage({
      content:
        "Glad I could help. This conversation is now closed. You can start a new support question.",
    });
  }

  function handleNotResolved(messageId: string, originalQuery: string) {
    deactivateActionButtons(messageId);

    const escalationMessageId = createMessageId();

    const escalationMessage: ChatMessage = {
      id: escalationMessageId,
      role: "assistant",
      content: "Would you like to request human support?",
      actionType: "escalation",
      isActionActive: true,
      toolResult: {
        original_query: originalQuery,
        conversation_action: "ask_escalation",
      },
    };

    setMessages((currentMessages) => [
      ...currentMessages,
      escalationMessage,
    ]);

    setPendingAction({
      messageId: escalationMessageId,
      type: "escalation",
      originalQuery,
    });
  }

  async function handleRequestHumanSupport(
    messageId: string,
    originalQuery: string
  ) {
    deactivateActionButtons(messageId);
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await fetch(`${API_BASE_URL}/tickets/escalate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          original_question: originalQuery,
          reason: "user_requested_human_support",
        }),
      });

      if (!response.ok) {
        throw new Error(`Escalation failed with status ${response.status}`);
      }

      const data: {
        message: string;
        ticket?: unknown;
        reason?: string | null;
      } = await response.json();

      addAssistantMessage({
        content:
          `${data.message} This conversation is now closed. ` +
          "You can start a new support question.",
        toolUsed: "create_support_ticket",
        toolResult: {
          ticket: data.ticket,
          reason: data.reason,
        },
      });

      setPendingAction(null);
    } catch (error) {
      console.error(error);

      setErrorMessage(
        "Sorry, something went wrong while requesting human support."
      );
    } finally {
      setIsLoading(false);
    }
  }

  function handleEndChat(messageId: string) {
    deactivateActionButtons(messageId);
    setPendingAction(null);

    addAssistantMessage({
      content:
        "This conversation has been closed. You can start a new support question.",
    });
  }

  return (
    <section className="chat-panel">
      <h2>Support Chat</h2>

      <div className="chat-messages">
        {messages.map((message) => {
          const originalQuery =
            typeof message.toolResult?.original_query === "string"
              ? message.toolResult.original_query
              : pendingAction?.originalQuery ?? "";

          const shouldShowSources =
            message.toolResult?.sources &&
            message.toolResult.sources.length > 0;

          return (
            <div
              key={message.id}
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

              {shouldShowSources && (
                <div className="sources">
                  <div className="sources-title">Sources</div>

                  {message.toolResult?.sources?.map((source, sourceIndex) => (
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

              {message.isActionActive &&
                message.actionType === "resolution_feedback" && (
                  <div className="conversation-actions">
                    <div className="conversation-actions-title">
                      Did this solve your issue?
                    </div>

                    <button
                      type="button"
                      onClick={() => handleResolved(message.id)}
                      disabled={isLoading}
                    >
                      Yes, solved
                    </button>


                    <button
                      type="button"
                      onClick={() =>
                        handleNotResolved(message.id, originalQuery)
                      }
                      disabled={isLoading}
                    >
                      No, I need help
                    </button>
                  </div>
                )}

              {message.isActionActive &&
                message.actionType === "escalation" && (
                  <div className="conversation-actions">
                    <button
                      type="button"
                      onClick={() =>
                        void handleRequestHumanSupport(
                          message.id,
                          originalQuery
                        )
                      }
                      disabled={isLoading}
                    >
                      Request human support
                    </button>

                    <button
                      type="button"
                      onClick={() => handleEndChat(message.id)}
                      disabled={isLoading}
                    >
                      End chat
                    </button>
                  </div>
                )}
            </div>
          );
        })}

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
          placeholder={
            isInputLocked
              ? "Please choose an option above to continue..."
              : "Ask about your order, return policy, refund time, or delivery..."
          }
          rows={3}
          disabled={isLoading || isInputLocked}
        />

        <button
          type="button"
          onClick={handleSendMessage}
          disabled={
            isLoading ||
            isInputLocked ||
            input.trim().length === 0
          }
        >
          {isLoading ? "Sending..." : "Send"}
        </button>
      </div>
    </section>
  );
}