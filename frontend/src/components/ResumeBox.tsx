import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { ResumeStatus } from "../types";

/** Shows which resume fit/tailoring runs against, and lets the user swap it. */
export default function ResumeBox({ onChange }: { onChange?: () => void }) {
  const [status, setStatus] = useState<ResumeStatus | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const input = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.resumeStatus().then(setStatus).catch(() => setError("Couldn't load resume status"));
  }, []);

  async function act(fn: () => Promise<ResumeStatus>) {
    setBusy(true);
    setError("");
    try {
      setStatus(await fn());
      onChange?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "failed");
    } finally {
      setBusy(false);
      if (input.current) input.current.value = "";
    }
  }

  const label = !status
    ? "Loading…"
    : status.is_sample
      ? "Sample profile (not you) — upload your resume for real results"
      : status.filename ?? status.source;

  return (
    <div className={`card ${status?.is_sample ? "warn" : ""}`}>
      <div className="row">
        <div style={{ flex: 1 }}>
          <strong>Resume:</strong> {label}
          {status && !status.is_sample && (
            <div className="muted small">{status.skills.length} skills detected</div>
          )}
        </div>
        <input
          ref={input}
          type="file"
          accept=".pdf,.docx,.txt,.md"
          hidden
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) act(() => api.resumeUpload(f));
          }}
        />
        <button disabled={busy} onClick={() => input.current?.click()}>
          {busy ? "Working…" : status?.is_sample ? "Upload resume" : "Replace"}
        </button>
        {status?.source === "uploaded" && (
          <button disabled={busy} onClick={() => act(api.resumeRemove)}>
            Remove
          </button>
        )}
      </div>
      {error && <p className="error small">{error}</p>}
    </div>
  );
}
