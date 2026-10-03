export interface JDFields {
  title: string;
  company: string;
  location: string;
  work_type: string;
  salary: string;
  required_skills: string[];
  visa_language: string[];
  seniority_hint: string;
}

export interface FitResult {
  score: number;
  verdict: string;
  matched_skills: string[];
  gap_skills: string[];
}

export interface TailoredBullet {
  original: string;
  tailored: string;
  changed: boolean;
  relevant_skills?: string[];
  why?: string;
}

export interface OutreachDraft {
  connection_note: string;
  connection_note_chars: number;
  followup_message: string;
  angle: string;
}

export interface PipelineResult {
  jd: JDFields;
  fit: FitResult;
  tailored: { bullets: TailoredBullet[]; changed_count: number; demo_mode: boolean };
  outreach: OutreachDraft;
  top_skills: TopSkill[];
  interview: { questions: string[] };
  common_questions: QuestionBank;
}

export interface QuestionBank {
  behavioral: string[];
  technical: { skill: string; questions: string[] }[];
}

export interface TopSkill {
  skill: string;
  mentions: number;
  on_resume: boolean;
}

export interface SavedJob {
  id: number;
  title: string;
  company: string;
  url: string;
  fit_score: number | null;
  verdict: string;
  top_skills: TopSkill[];
  gaps: string[];
  questions: string[];
  notes: string;
  resume: string;
  saved_at: number;
}

export interface JobListing {
  source: string;
  title: string;
  company: string;
  location: string;
  url: string;
  description: string;
  posted_at: string;
}

export interface Application {
  id: number;
  company: string;
  role: string;
  url: string;
  location: string;
  date_applied: string;
  status: string;
  notes: string;
}

export const STATUSES = [
  "applied",
  "screening",
  "interview",
  "offer",
  "rejected",
  "withdrawn",
];

export interface ResumeStatus {
  source: string;
  is_sample: boolean;
  filename: string | null;
  skills: string[];
}
