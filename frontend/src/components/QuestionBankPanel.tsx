import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import type { QuestionBank } from "../types";
import QuestionList from "./QuestionList";

export default function QuestionBankPanel() {
  const [bank, setBank] = useState<QuestionBank | null>(null);
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api.questionBank().then(setBank).catch((e) => setError(String(e)));
  }, []);

  const filtered = useMemo<QuestionBank | null>(() => {
    if (!bank) return null;
    const q = query.trim().toLowerCase();
    if (!q) return bank;
    const match = (s: string) => s.toLowerCase().includes(q);
    return {
      behavioral: bank.behavioral.filter(match),
      technical: bank.technical
        .map((t) => ({ ...t, questions: match(t.skill) ? t.questions : t.questions.filter(match) }))
        .filter((t) => t.questions.length > 0),
    };
  }, [bank, query]);

  return (
    <div>
      <h2>Most-asked interview questions</h2>
      <p className="muted">
        Commonly asked questions by skill, plus behavioral/HR questions asked in
        almost every interview. Search by skill (e.g. "react", "sql") or keyword.
      </p>
      <input
        placeholder="Search skills or questions…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      {error && <p className="error">{error}</p>}
      {filtered && (
        filtered.technical.length + filtered.behavioral.length === 0 ? (
          <p className="muted">No questions match "{query}".</p>
        ) : (
          <QuestionList bank={filtered} openFirst={query ? 99 : 0} />
        )
      )}
    </div>
  );
}
