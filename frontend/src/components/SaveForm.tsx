import { useEffect, useState } from "react";
import { api } from "../api";
import type { PipelineResult } from "../types";

/** "Add to table": saves this analysis to the Saved Jobs table. Title and
 *  company are editable because partial postings often lack them. */
export default function SaveForm({ result }: { result: PipelineResult }) {
  const [title, setTitle] = useState(result.jd.title);
  const [company, setCompany] = useState(result.jd.company);
  const [url, setUrl] = useState("");
  const [notes, setNotes] = useState("");
  const [state, setState] = useState<"idle" | "saving" | "saved">("idle");
  const [error, setError] = useState("");

  // New analysis → fresh form.
  useEffect(() => {
    setTitle(result.jd.title);
    setCompany(result.jd.company);
    setUrl("");
    setNotes("");
    setState("idle");
    setError("");
  }, [result]);

  async function save() {
    setState("saving");
    setError("");
    try {
      const resume = await api.resumeStatus().catch(() => null);
      await api.savedAdd({
        title: title.trim(),
        company: company.trim(),
        url: url.trim(),
        notes: notes.trim(),
        fit_score: result.fit.score,
        verdict: result.fit.verdict,
        top_skills: result.top_skills,
        gaps: result.top_skills.filter((s) => !s.on_resume).map((s) => s.skill),
        questions: result.interview.questions,
        resume: resume?.filename ?? (resume?.is_sample ? "sample profile" : ""),
      });
      setState("saved");
    } catch (e) {
      setError(e instanceof Error ? e.message : "failed");
      setState("idle");
    }
  }

  if (state === "saved") {
    return (
      <p className="good save-done">
        ✓ Added to your table — open the <strong>Saved Jobs</strong> tab to view
        it or download the PDF.
      </p>
    );
  }

  return (
    <div className="save-form">
      <h4>Add to table</h4>
      <div className="row">
        <input placeholder="Job title (required)" value={title}
               onChange={(e) => setTitle(e.target.value)} />
        <input placeholder="Company" value={company}
               onChange={(e) => setCompany(e.target.value)} />
      </div>
      <div className="row">
        <input placeholder="Posting link (optional)" value={url}
               onChange={(e) => setUrl(e.target.value)} />
        <input placeholder="Notes (optional)" value={notes}
               onChange={(e) => setNotes(e.target.value)} />
        <button onClick={save} disabled={state === "saving" || !title.trim()}>
          {state === "saving" ? "Saving…" : "Add to table"}
        </button>
      </div>
      {error && <p className="error small">{error}</p>}
    </div>
  );
}
