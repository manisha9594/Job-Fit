import { useState } from "react";
import { api } from "../api";
import type { PipelineResult } from "../types";
import ResumeBox from "./ResumeBox";
import QuestionList from "./QuestionList";
import SaveForm from "./SaveForm";
import TailorSection from "./TailorSection";

export default function JDPanel() {
  const [jdText, setJdText] = useState("");
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function run() {
    setLoading(true);
    setError("");
    try {
      setResult(await api.pipeline(jdText));
    } catch (e) {
      setError(e instanceof Error ? e.message : "failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2>Analyze a job posting</h2>
      <p className="muted">
        Paste the full posting text. The pipeline extracts fields, scores fit
        against your resume, tailors bullets, and drafts outreach.
      </p>
      {/* Results were scored against the old resume, so clear them on change. */}
      <ResumeBox onChange={() => setResult(null)} />
      <textarea
        rows={10}
        placeholder="Paste job description here…"
        value={jdText}
        onChange={(e) => setJdText(e.target.value)}
      />
      <div className="row">
        <button onClick={run} disabled={loading || jdText.trim().length < 20}>
          {loading ? "Analyzing…" : "Analyze"}
        </button>
      </div>
      {error && <p className="error">{error}</p>}
      {result && (
        <div className="card">
          <h3>
            {result.jd.title || "Untitled role"}
            {result.jd.company && ` @ ${result.jd.company}`}
          </h3>
          <p className="muted">
            {[
              result.jd.location,
              result.jd.work_type !== "unknown" && result.jd.work_type,
              result.jd.salary || "salary not listed",
            ]
              .filter(Boolean)
              .join(" · ")}
          </p>
          <div className="fitbar">
            <div className="fill" style={{ width: `${result.fit.score}%` }} />
          </div>
          <p>
            <strong>{result.fit.score}/100</strong> — {result.fit.verdict}
          </p>
          <h4>Top skills for this role</h4>
          {result.top_skills.length === 0 ? (
            <p className="muted small">
              No known skills found — paste the full posting, including the
              requirements section.
            </p>
          ) : (
            <table className="skills">
              <thead>
                <tr><th>#</th><th>Skill</th><th>Mentions</th><th>Your resume</th></tr>
              </thead>
              <tbody>
                {result.top_skills.map((s, i) => (
                  <tr key={s.skill}>
                    <td className="muted">{i + 1}</td>
                    <td><strong>{s.skill}</strong></td>
                    <td>{s.mentions}×</td>
                    <td className={s.on_resume ? "good" : "bad"}>
                      {s.on_resume ? "✓ on resume" : "✗ gap — prepare for this"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {result.jd.visa_language.length > 0 && (
            <div>
              <h4>⚠ Visa / work-authorization language (verbatim)</h4>
              <ul>
                {result.jd.visa_language.map((q, i) => (
                  <li key={i} className="quote">
                    {q}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <h4>Interview prep — questions for this role</h4>
          <ol className="questions">
            {result.interview.questions.map((q, i) => (
              <li key={i}>{q}</li>
            ))}
          </ol>
          <h4>Most-asked questions for this job's skills</h4>
          <QuestionList bank={result.common_questions} openFirst={1} />
          <SaveForm result={result} />
          <TailorSection result={result} />
          <details>
            <summary className="muted">More: LinkedIn outreach drafts</summary>
          <h4>Outreach drafts</h4>
          <p className="muted">Connection note ({result.outreach.connection_note_chars}/300):</p>
          <p className="draft">{result.outreach.connection_note}</p>
          <p className="muted">Follow-up:</p>
          <p className="draft">{result.outreach.followup_message}</p>
          <p className="muted small">
            Drafts only — review and send them yourself. This app never sends messages.
          </p>
          </details>
        </div>
      )}
    </div>
  );
}
