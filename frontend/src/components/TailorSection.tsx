import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import type { PipelineResult } from "../types";

type Filter = "changed" | "relevant" | "all";

/** Review AI bullet rewrites (or edit by hand), then download your .docx
 *  resume with the accepted bullets replaced in place. */
export default function TailorSection({ result }: { result: PipelineResult }) {
  const bullets = result.tailored.bullets;
  const [text, setText] = useState<string[]>([]);
  const [use, setUse] = useState<boolean[]>([]);
  const [filter, setFilter] = useState<Filter>("changed");
  const [isDocx, setIsDocx] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    setText(bullets.map((b) => b.tailored));
    setUse(bullets.map((b) => b.changed));
    setFilter(result.tailored.changed_count > 0 ? "changed" : "relevant");
    setMsg("");
    api
      .resumeStatus()
      .then((s) => setIsDocx(!!s.filename?.toLowerCase().endsWith(".docx")))
      .catch(() => setIsDocx(null));
  }, [result]);

  const shown = useMemo(
    () =>
      bullets
        .map((b, i) => ({ b, i }))
        .filter(({ b, i }) =>
          filter === "all" ? true
          : filter === "changed" ? b.changed || use[i]
          : (b.relevant_skills?.length ?? 0) > 0 || b.changed || use[i]
        ),
    [bullets, filter, use]
  );

  const accepted = bullets
    .map((b, i) => ({ original: b.original, tailored: text[i] ?? b.tailored, on: use[i] }))
    .filter((e) => e.on && e.tailored.trim() && e.tailored.trim() !== e.original.trim());

  function edit(i: number, value: string) {
    setText((t) => t.map((v, j) => (j === i ? value : v)));
    setUse((u) => u.map((v, j) => (j === i ? value.trim() !== bullets[i].original.trim() : v)));
  }

  async function download() {
    setBusy(true);
    setMsg("");
    try {
      const { blob, name } = await api.tailoredResume(
        accepted.map(({ original, tailored }) => ({ original, tailored })),
        result.jd.company
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = name;
      a.click();
      URL.revokeObjectURL(url);
      setMsg(`✓ Downloaded ${name} with ${accepted.length} bullet(s) updated.`);
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Download failed");
    } finally {
      setBusy(false);
    }
  }

  const count = (f: Filter) =>
    f === "all" ? bullets.length
    : f === "changed" ? bullets.filter((b, i) => b.changed || use[i]).length
    : bullets.filter((b, i) => (b.relevant_skills?.length ?? 0) > 0 || b.changed || use[i]).length;

  return (
    <div className="tailor">
      <h4>Tailor your resume for this job</h4>
      {result.tailored.demo_mode ? (
        <p className="muted small warn-text">
          AI rewriting is off (DEMO mode — no API key yet), so no bullets were
          changed. You can still edit any bullet below by hand; bullets that
          already show this job's skills are under "Relevant".
        </p>
      ) : (
        <p className="muted small">
          {result.tailored.changed_count} bullet(s) rewritten for this job. Review
          each one — edit freely, untick any you don't want.
        </p>
      )}

      <div className="row filters">
        {(["changed", "relevant", "all"] as Filter[]).map((f) => (
          <button key={f} className={filter === f ? "active" : ""} onClick={() => setFilter(f)}>
            {f === "changed" ? "Suggested changes" : f === "relevant" ? "Relevant to job" : "All bullets"}{" "}
            ({count(f)})
          </button>
        ))}
      </div>

      {shown.length === 0 && (
        <p className="muted small">Nothing here — try "All bullets".</p>
      )}
      {shown.map(({ b, i }) => {
        const changed = (text[i] ?? b.tailored).trim() !== b.original.trim();
        return (
          <div key={i} className={`tbullet ${use[i] && changed ? "on" : ""}`}>
            <label className="small">
              <input
                type="checkbox"
                checked={!!use[i]}
                disabled={!changed}
                onChange={(e) => setUse((u) => u.map((v, j) => (j === i ? e.target.checked : v)))}
              />{" "}
              {changed ? "Use this version" : "Unchanged"}
              {b.relevant_skills && b.relevant_skills.length > 0 && (
                <span className="muted"> · shows {b.relevant_skills.join(", ")}</span>
              )}
              {b.why && <span className="muted"> · {b.why}</span>}
            </label>
            {changed && <div className="orig small">Was: {b.original}</div>}
            <textarea
              rows={Math.min(4, Math.ceil((text[i] ?? "").length / 95) + 1)}
              value={text[i] ?? ""}
              onChange={(e) => edit(i, e.target.value)}
            />
            {changed && (
              <button className="linklike small" onClick={() => edit(i, b.original)}>
                ↺ revert to original
              </button>
            )}
          </div>
        );
      })}

      <div className="row download">
        <button onClick={download} disabled={busy || !accepted.length || isDocx === false}>
          {busy ? "Preparing…" : `⬇ Download tailored resume (.docx) — ${accepted.length} change(s)`}
        </button>
      </div>
      {isDocx === false && (
        <p className="muted small warn-text">
          Download needs a Word (.docx) resume so your formatting can be kept —
          upload one in the Resume box above.
        </p>
      )}
      {msg && <p className="small">{msg}</p>}
    </div>
  );
}
