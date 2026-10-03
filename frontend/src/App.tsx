import { useEffect, useState } from "react";
import { api } from "./api";
import JDPanel from "./components/JDPanel";
import QuestionBankPanel from "./components/QuestionBankPanel";
import SavedPanel from "./components/SavedPanel";
import "./styles.css";

// Tracker, Find Jobs and Interview Prep panels still exist in components/ but
// are hidden for now: job search needs external portal APIs, interview prep is
// part of Analyze JD + Question Bank, and the tracker comes later.
const TABS = ["Analyze JD", "Saved Jobs", "Question Bank"] as const;

export default function App() {
  const [tab, setTab] = useState<(typeof TABS)[number]>("Analyze JD");
  const [health, setHealth] = useState("");

  useEffect(() => {
    api
      .health()
      .then((h) =>
        setHealth(
          `${h.demo_mode ? "DEMO" : h.llm_provider.toUpperCase()} mode`
        )
      )
      .catch(() => setHealth("backend offline"));
  }, []);

  return (
    <div className="app">
      <header>
        <h1>🎯 JobFit</h1>
        <span className="badge">{health}</span>
      </header>
      <nav>
        {TABS.map((t) => (
          <button
            key={t}
            className={tab === t ? "active" : ""}
            onClick={() => setTab(t)}
          >
            {t}
          </button>
        ))}
      </nav>
      <main>
        {tab === "Analyze JD" && <JDPanel />}
        {tab === "Saved Jobs" && <SavedPanel />}
        {tab === "Question Bank" && <QuestionBankPanel />}
      </main>
      <footer className="muted small">
        Drafts and scores are advisory. This app never submits applications or
        sends messages — you review everything and click send.
      </footer>
    </div>
  );
}
