import { Check, Send, Sparkles, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import { clearPendingExtraction, pushUserMessage, sendChatMessage } from "../redux/chatSlice";
import { createInteraction, deleteInteraction, purgeAll, purgeOne } from "../redux/interactionsSlice";

export default function ChatPanel() {
  const dispatch = useDispatch();
  const { messages, isTyping, pendingExtraction, error } = useSelector((state) => state.chat);
  const { deletedIds } = useSelector((state) => state.interactions);
  const [message, setMessage] = useState("");
  const latestAssistant = useMemo(() => [...messages].reverse().find((row) => row.role === "assistant"), [messages]);

  // Sync agent-initiated deletes to Redux state (backend already deleted; no API call needed)
  useEffect(() => {
    if (!latestAssistant || latestAssistant.action !== "delete") return;
    if (latestAssistant.toolOutput?.deleted_all) {
      dispatch(purgeAll());
    } else if (latestAssistant.toolOutput?.interaction_id && latestAssistant.toolOutput?.deleted) {
      dispatch(purgeOne(latestAssistant.toolOutput.interaction_id));
    }
  }, [latestAssistant]);

  const submit = (event) => {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed || isTyping) return;
    dispatch(pushUserMessage(trimmed));
    dispatch(sendChatMessage(trimmed));
    setMessage("");
  };

  const confirmExtraction = () => {
    if (!pendingExtraction) return;
    dispatch(createInteraction(pendingExtraction));
    dispatch(clearPendingExtraction());
  };

  const handleDelete = (interactionId) => {
    if (window.confirm(`Delete interaction #${interactionId}? This cannot be undone.`)) {
      dispatch(deleteInteraction(interactionId));
    }
  };

  const isDeleted = (interactionId) => deletedIds.includes(interactionId);

  return (
    <section className="panel chat-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Conversational Entry</p>
          <h2>CRM Assistant</h2>
        </div>
        <div className="model-chip">
          <Sparkles size={16} />
          <span>gemma2-9b-it</span>
        </div>
      </div>

      <div className="messages" aria-live="polite">
        {messages.length === 0 && (
          <div className="empty-state">
            <p>Try: Met Dr. Patel today about Product X. Sentiment positive. Follow up next week.</p>
          </div>
        )}
        {messages.map((row, index) => (
          <article key={`${row.role}-${index}`} className={`message ${row.role}`}>
            <p>{row.content}</p>
            {row.action === "log" && row.extractedData && Object.keys(row.extractedData).length > 0 && (
              <pre>{JSON.stringify(row.extractedData, null, 2)}</pre>
            )}
            {row.action === "edit" && row.toolOutput?.record && (
              <pre>{JSON.stringify(row.toolOutput.record, null, 2)}</pre>
            )}
            {row.action === "search" && row.toolOutput?.interactions?.length > 0 && (
              <pre>{JSON.stringify(row.toolOutput.interactions, null, 2)}</pre>
            )}
            {row.action === "log" && row.interactionId && (
              <div className="saved-row">
                {isDeleted(row.interactionId) ? (
                  <span className="saved-pill deleted">Deleted #{row.interactionId}</span>
                ) : (
                  <>
                    <span className="saved-pill">Saved #{row.interactionId}</span>
                    <button
                      className="icon-button danger small"
                      type="button"
                      title="Delete this interaction"
                      onClick={() => handleDelete(row.interactionId)}
                    >
                      <Trash2 size={14} />
                    </button>
                  </>
                )}
              </div>
            )}
          </article>
        ))}
        {isTyping && <article className="message assistant"><p>Working...</p></article>}
        {error && <p className="error-line">{error}</p>}
      </div>

      {pendingExtraction && latestAssistant && !latestAssistant.interactionId && (
        <button className="confirm-button" type="button" onClick={confirmExtraction}>
          <Check size={18} />
          <span>Confirm & Save</span>
        </button>
      )}

      <form className="chat-input-row" onSubmit={submit}>
        <input
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="Type an interaction, edit, search, follow-up, delete, or summary request"
        />
        <button className="icon-button primary square" type="submit" disabled={isTyping} title="Send message">
          <Send size={18} />
        </button>
      </form>
    </section>
  );
}

