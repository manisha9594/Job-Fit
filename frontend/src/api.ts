import type {
  Application,
  JobListing,
  PipelineResult,
  QuestionBank,
  ResumeStatus,
  SavedJob,
} from "./types";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!r.ok) {
    const body = await r.text();
    throw new Error(`API ${r.status}: ${body.slice(0, 200)}`);
  }
  return r.json() as Promise<T>;
}

export const api = {
  health: () => req<{ status: string; demo_mode: boolean; llm_provider: string }>("/health"),
  resumeStatus: () => req<ResumeStatus>("/resume/status"),
  resumeUpload: async (file: File) => {
    // No JSON Content-Type here: the browser sets the multipart boundary.
    const form = new FormData();
    form.append("file", file);
    const r = await fetch("/api/resume/upload", { method: "POST", body: form });
    if (!r.ok) {
      const body = await r.json().catch(() => ({}));
      throw new Error(body.detail ?? `Upload failed (${r.status})`);
    }
    return (await r.json()) as ResumeStatus;
  },
  tailoredResume: async (edits: { original: string; tailored: string }[], company: string) => {
    const r = await fetch("/api/resume/tailored", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ edits, company }),
    });
    if (!r.ok) {
      const body = await r.json().catch(() => ({}));
      throw new Error(body.detail ?? `Download failed (${r.status})`);
    }
    const name =
      /filename="([^"]+)"/.exec(r.headers.get("Content-Disposition") ?? "")?.[1] ??
      "resume_tailored.docx";
    return { blob: await r.blob(), name };
  },
  resumeRemove: () => req<ResumeStatus>("/resume", { method: "DELETE" }),
  pipeline: (jd_text: string) =>
    req<PipelineResult>("/pipeline", {
      method: "POST",
      body: JSON.stringify({ jd_text }),
    }),
  questions: (jd_text: string) =>
    req<{ questions: string[] }>("/interview/questions", {
      method: "POST",
      body: JSON.stringify({ jd_text }),
    }),
  mock: (question: string, answer: string, jd_text: string) =>
    req<{ score: number; feedback: string[] }>("/interview/mock", {
      method: "POST",
      body: JSON.stringify({ question, answer, jd_text }),
    }),
  jobSearch: (params: Record<string, string>) =>
    req<{ source: string; jobs: JobListing[] }>(
      "/jobs/search?" + new URLSearchParams(params).toString()
    ),
  trackerList: () =>
    req<{ applications: Application[]; stats: { total: number } }>(
      "/tracker/applications"
    ),
  trackerAdd: (a: Partial<Application>) =>
    req<Application>("/tracker/applications", {
      method: "POST",
      body: JSON.stringify(a),
    }),
  trackerUpdate: (id: number, status: string) =>
    req<Application>(`/tracker/applications/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),
  trackerDelete: (id: number) =>
    req<{ deleted: number }>(`/tracker/applications/${id}`, {
      method: "DELETE",
    }),
  questionBank: () => req<QuestionBank>("/questions/bank"),
  savedList: () => req<{ jobs: SavedJob[] }>("/saved"),
  savedAdd: (job: Omit<SavedJob, "id" | "saved_at">) =>
    req<SavedJob>("/saved", { method: "POST", body: JSON.stringify(job) }),
  savedUpdate: (id: number, fields: Partial<Pick<SavedJob, "title" | "company" | "url" | "notes">>) =>
    req<SavedJob>(`/saved/${id}`, { method: "PATCH", body: JSON.stringify(fields) }),
  savedDelete: (id: number) =>
    req<{ deleted: number }>(`/saved/${id}`, { method: "DELETE" }),
  savedPdfUrl: "/api/saved/export.pdf",
  followups: () => req<{ due: Application[] }>("/tracker/followups"),
};
