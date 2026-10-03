import { useState } from "react";
import { api } from "../api";
import type { JobListing } from "../types";

const SOURCES = ["remotive", "arbeitnow", "greenhouse", "lever", "ashby"];

export default function JobsPanel() {
  const [source, setSource] = useState("remotive");
  const [query, setQuery] = useState("python ai engineer");
  const [board, setBoard] = useState("");
  const [jobs, setJobs] = useState<JobListing[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function run() {
    setLoading(true);
    setError("");
    try {
      const params: Record<string, string> = { source, query, limit: "20" };
      if (board) params.board = board;
      if (source === "lever" && board) params.company = board;
      const r = await api.jobSearch(params);
      setJobs(r.jobs);
    } catch (e) {
      setError(e instanceof Error ? e.message : "failed");
    } finally {
      setLoading(false);
    }
  }

  const needsBoard = ["greenhouse", "lever", "ashby"].includes(source);

  return (
    <div>
      <h2>Find jobs (read-only)</h2>
      <p className="muted">
        Pulls listings from free APIs and public career-page feeds. No logins,
        no auto-apply — open the posting and apply yourself.
      </p>
      <div className="row">
        <select value={source} onChange={(e) => setSource(e.target.value)}>
          {SOURCES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        {!needsBoard && (
          <input
            placeholder="keywords"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        )}
        {needsBoard && (
          <input
            placeholder={
              source === "lever" ? "company slug (e.g. netflix)" : "board slug (e.g. openai)"
            }
            value={board}
            onChange={(e) => setBoard(e.target.value)}
          />
        )}
        <button onClick={run} disabled={loading}>
          {loading ? "Searching…" : "Search"}
        </button>
      </div>
      {error && <p className="error">{error}</p>}
      <div className="jobs">
        {jobs.map((j, i) => (
          <div key={i} className="card job">
            <a href={j.url} target="_blank" rel="noreferrer">
              <strong>{j.title}</strong>
            </a>
            <div className="muted">
              {j.company} · {j.location} · {j.source}
            </div>
            {j.description && <p className="small">{j.description.slice(0, 220)}…</p>}
          </div>
        ))}
      </div>
      {jobs.length === 0 && !loading && <p className="muted">No results yet — run a search.</p>}
    </div>
  );
}
