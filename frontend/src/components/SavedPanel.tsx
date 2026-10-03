import { Fragment, useEffect, useState } from "react";
import { api } from "../api";
import type { SavedJob } from "../types";

export default function SavedPanel() {
  const [jobs, setJobs] = useState<SavedJob[] | null>(null);
  const [open, setOpen] = useState<number | null>(null);
  const [error, setError] = useState("");

  async function load() {
    try {
      setJobs((await api.savedList()).jobs);
    } catch (e) {
      setError(e instanceof Error ? e.message : "failed");
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function remove(job: SavedJob) {
    if (!confirm(`Remove "${job.title}" from the table?`)) return;
    await api.savedDelete(job.id);
    load();
  }

  async function saveNotes(job: SavedJob, notes: string) {
    if (notes === job.notes) return;
    const updated = await api.savedUpdate(job.id, { notes });
    setJobs((js) => js?.map((j) => (j.id === job.id ? updated : j)) ?? null);
  }

  return (
    <div>
      <div className="row">
        <h2 style={{ flex: 1, margin: 0 }}>Saved jobs</h2>
        <a
          className={`button ${jobs?.length ? "" : "disabled"}`}
          href={api.savedPdfUrl}
          download="saved-jobs.pdf"
        >
          ⬇ Download PDF
        </a>
      </div>
      <p className="muted">
        Jobs you added from Analyze JD. Click a row to see its interview
        questions. The PDF includes the table and every job's questions.
      </p>
      {error && <p className="error">{error}</p>}
      {jobs && jobs.length === 0 && (
        <div className="card muted">
          Nothing saved yet — analyze a job posting and click{" "}
          <strong>Add to table</strong>.
        </div>
      )}
      {jobs && jobs.length > 0 && (
        <table className="saved">
          <thead>
            <tr>
              <th>Saved</th><th>Role</th><th>Fit</th><th>Top skills</th>
              <th>Gaps</th><th>Notes</th><th></th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((j) => (
              <Fragment key={j.id}>
                <tr className="clickable" onClick={() => setOpen(open === j.id ? null : j.id)}>
                  <td className="muted small">
                    {new Date(j.saved_at * 1000).toLocaleDateString()}
                  </td>
                  <td>
                    <strong>{j.title}</strong>
                    {j.company && <div className="muted small">{j.company}</div>}
                    {j.url && (
                      <a href={j.url} target="_blank" rel="noreferrer" className="small"
                         onClick={(e) => e.stopPropagation()}>
                        posting ↗
                      </a>
                    )}
                  </td>
                  <td>{j.fit_score ?? "—"}</td>
                  <td className="small">{j.top_skills.map((s) => s.skill).join(", ")}</td>
                  <td className="small bad">{j.gaps.join(", ")}</td>
                  <td onClick={(e) => e.stopPropagation()}>
                    <input
                      defaultValue={j.notes}
                      placeholder="add notes…"
                      onBlur={(e) => saveNotes(j, e.target.value)}
                    />
                  </td>
                  <td onClick={(e) => e.stopPropagation()}>
                    <button className="danger" title="Remove" onClick={() => remove(j)}>
                      ✕
                    </button>
                  </td>
                </tr>
                {open === j.id && (
                  <tr>
                    <td colSpan={7}>
                      <strong>Interview prep</strong>
                      {j.resume && <span className="muted small"> · scored against {j.resume}</span>}
                      <ol className="questions">
                        {j.questions.map((q, i) => <li key={i}>{q}</li>)}
                      </ol>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
