import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, MessageSquarePlus, Send } from "lucide-react";
import { getChatHistory, listSessions, sendChatMessage } from "../services/api";

export default function ChatPage() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [chatId, setChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [messageInput, setMessageInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);

  const sortedSessions = useMemo(
    () => [...sessions].sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at)),
    [sessions]
  );

  const fetchSessions = async () => {
    setLoading(true);
    try {
      const data = await listSessions();
      const allSessions = data.sessions || [];
      setSessions(allSessions);
      return allSessions;
    } finally {
      setLoading(false);
    }
  };

  const openSession = async (sessionId) => {
    setChatId(sessionId);
    const data = await getChatHistory(sessionId);
    setMessages(data.history || []);
  };

  const handleNewChat = () => {
    setChatId(null);
    setMessages([]);
    setMessageInput("");
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!messageInput.trim()) return;

    const text = messageInput.trim();
    setMessageInput("");
    setSending(true);

    try {
      const response = await sendChatMessage(text, chatId);
      const refreshedSessions = await fetchSessions();

      const selectedChatId =
        response?.chat_id ||
        chatId ||
        refreshedSessions?.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))[0]?.chat_id;

      if (selectedChatId) {
        setChatId(selectedChatId);
        const history = await getChatHistory(selectedChatId);
        setMessages(history.history || []);
      }
    } finally {
      setSending(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  return (
    <div className="chat-layout">
      <aside className="chat-sidebar">
        <div className="chat-sidebar-top">
          <button className="secondary-btn" onClick={() => navigate("/")}> 
            <ArrowLeft size={16} /> Back
          </button>
          <button className="primary-btn" onClick={handleNewChat}>
            <MessageSquarePlus size={16} /> New Chat
          </button>
        </div>

        <h3>Sessions</h3>
        {loading && <p className="muted">Loading sessions...</p>}
        <ul className="sessions-list">
          {sortedSessions.map((s) => (
            <li key={s.chat_id}>
              <button
                className={`session-btn ${chatId === s.chat_id ? "active" : ""}`}
                onClick={() => openSession(s.chat_id)}
              >
                <span>{s.chat_id.slice(0, 10)}...</span>
                <small>{s.message_count || 0} msgs</small>
              </button>
            </li>
          ))}
        </ul>
      </aside>

      <section className="chat-main">
        <header className="chat-header">
          <h2>PhysioAssist Chat</h2>
          <p className="muted">Describe symptoms and get guidance.</p>
        </header>

        <div className="messages-panel">
          {!messages.length && (
            <div className="empty-state">Start a new conversation with PhysioAssist.</div>
          )}
          {messages.map((msg, idx) => (
            <div key={`${msg.timestamp || idx}-${idx}`} className={`msg-bubble ${msg.role}`}>
              <p>{msg.content}</p>
            </div>
          ))}
        </div>

        <form className="message-form" onSubmit={handleSend}>
          <input
            type="text"
            placeholder="Type your message..."
            value={messageInput}
            onChange={(e) => setMessageInput(e.target.value)}
          />
          <button className="primary-btn" type="submit" disabled={sending}>
            <Send size={16} /> {sending ? "Sending..." : "Send"}
          </button>
        </form>
      </section>
    </div>
  );
}
