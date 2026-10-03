import type { QuestionBank } from "../types";

/** Most-asked questions grouped by skill, each group collapsible. */
export default function QuestionList({
  bank,
  openFirst = 0,
}: {
  bank: QuestionBank;
  openFirst?: number;
}) {
  return (
    <div className="qlist">
      {bank.technical.map((t, i) => (
        <details key={t.skill} open={i < openFirst}>
          <summary>
            <strong>{t.skill}</strong>{" "}
            <span className="muted small">({t.questions.length})</span>
          </summary>
          <ol className="questions">
            {t.questions.map((q) => <li key={q}>{q}</li>)}
          </ol>
        </details>
      ))}
      {bank.behavioral.length > 0 && (
        <details open={bank.technical.length === 0}>
          <summary>
            <strong>Behavioral / HR</strong>{" "}
            <span className="muted small">({bank.behavioral.length})</span>
          </summary>
          <ol className="questions">
            {bank.behavioral.map((q) => <li key={q}>{q}</li>)}
          </ol>
        </details>
      )}
    </div>
  );
}
