import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { LogOut, MessageCircle, Search, UploadCloud } from "lucide-react";
import { runIngestion, searchInjuries } from "../services/api";
import { useAuth } from "../context/AuthContext";

export default function HomePage() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [recreateIndex, setRecreateIndex] = useState(false);

  const hasResults = useMemo(() => results.length > 0, [results]);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    setStatusMessage("");
    try {
      const data = await searchInjuries(query.trim());
      setResults(data.results || []);
      if (!data.results?.length) setStatusMessage("No results found.");
    } catch {
      setStatusMessage("Search failed. Please try again.");
      setResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleIngestion = async () => {
    setIngesting(true);
    setStatusMessage("");
    try {
      const data = await runIngestion(recreateIndex);
      setStatusMessage(
        data.success
          ? `Ingestion done: ${data.documents_indexed}/${data.documents_fetched} indexed.`
          : "Ingestion failed."
      );
    } catch {
      setStatusMessage("Ingestion failed. Please check backend logs.");
    } finally {
      setIngesting(false);
    }
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-left">
          <button className="primary-btn" onClick={handleIngestion} disabled={ingesting}>
            <UploadCloud size={16} />
            {ingesting ? "Running..." : "Data Ingestion"}
          </button>
          <label className="toggle-label">
            <input
              type="checkbox"
              checked={recreateIndex}
              onChange={(e) => setRecreateIndex(e.target.checked)}
            />
            Recreate index
          </label>
        </div>

        <form className="search-form" onSubmit={handleSearch}>
          <Search size={16} />
          <input
            type="text"
            placeholder="Search injuries, symptoms, treatments..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button type="submit" className="secondary-btn" disabled={searching}>
            {searching ? "Searching..." : "Search"}
          </button>
        </form>

        <button className="icon-btn" onClick={logout} title="Logout">
          <LogOut size={18} />
        </button>
      </header>

      <main className="content-area">
        <section className="results-panel">
          <h2>Search Results</h2>
          {statusMessage && <p className="muted">{statusMessage}</p>}

          {!hasResults && !statusMessage && (
            <div className="empty-state">Start with a search to discover injury data.</div>
          )}

          {hasResults && (
            <ul className="results-list">
              {results.map((item, idx) => (
                <li key={`${item.document?.title || "result"}-${idx}`} className="result-card">
                  <div className="result-head">
                    <h3>{item.document?.title || "Untitled"}</h3>
                    <span className="score-chip">{(item.score || 0).toFixed(2)}</span>
                  </div>
                  <p>{item.document?.content || "No content"}</p>
                  {!!item.document?.tags?.length && (
                    <div className="tag-row">
                      {item.document.tags.map((tag) => (
                        <span className="tag" key={`${tag}-${idx}`}>{tag}</span>
                      ))}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>

      <button className="chat-fab" onClick={() => navigate("/chat")} title="Open chat">
        <MessageCircle size={22} />
      </button>
    </div>
  );
}
