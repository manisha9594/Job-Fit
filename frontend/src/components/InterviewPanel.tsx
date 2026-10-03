import { useState } from "react";
import { api } from "../api";

export default function InterviewPanel() {
  const [jdText, setJdText] = useState("");
  const [questions, setQuestions] = useState<string[]>([]);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [score, setScore] = useState<number | null>(null);
  const [feedback, setFeedback] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  async function gen() {
    setLoading(true);
    try {
      const r = await api.questions(jdText);
      setQuestions(r.questions);
      if (r.questions.length > 0) setQuestion(r.questions[0]);
    } finally {
      setLoading(false);
    }
  }

  async function runMock() {
    setLoading(true);
    try {
      const r = await api.mock(question, answer, jdText);
      setScore(r.score);
      setFeedback(r.feedback);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2>Interview prep</h2>
      <p className="muted">
        Paste a job posting to generate likely questions, then practice answers
        and get scored.
      </p>
      <textarea
        rows={6}
        placeholder="Paste job description here…"
        value={jdText}
        onChange={(e) => setJdText(e.target.value)}
      />
      <div className="row">
        <button onClick={gen} disabled={loading || jdText.trim().length < 20}>
          Generate questions
        </button>
      </div>
      {questions.length > 0 && (
        <div className="card">
          <h4>Likely questions</h4>
          <ol>
            {questions.map((q, i) => (
              <li key={i}>
                <button className="linklike" onClick={() => setQuestion(q)}>
                  {q}
                </button>
              </li>
            ))}
          </ol>
          <h4>Mock answer</h4>
          <p className="muted small">{question}</p>
          <textarea
            rows={5}
            placeholder="Type your answer (STAR format works best)…"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
          />
          <div className="row">
            <button onClick={runMock} disabled={loading || !answer.trim()}>
              Score my answer
            </button>
          </div>
          {score !== null && (
            <div>
              <p>
                <strong>Score: {score}/100</strong>
              </p>
              <ul>
                {feedback.map((f, i) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
