const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

export type Domain = 'NCD' | 'MH';

export interface AnalyzePayload {
  age: number;
  sex: 'M' | 'F' | 'Other';
  domain: Domain;
  primary_symptom: string;
  duration_days?: number;
  bp_sys?: number | null;
  bp_dia?: number | null;
  glucose?: number | null;
  phq9?: number | null;
  gad7?: number | null;
  weight?: number | null;
  red_flag_answers: {
    self_harm: boolean;
  };
}

export interface AnalyzeResponse {
  triage_level: 'แดง' | 'ส้ม' | 'เหลือง' | 'เขียว';
  actions: string[];
  rationale: string[];
  condition_hints: string[];
}

export interface TrendResponse {
  points: { date: string; value: number }[];
  ewma: number | null;
  slope_per_day: number | null;
  trend: 'ดีขึ้น' | 'ทรงตัว' | 'แย่ลง' | 'ไม่เพียงพอ';
  confidence: number;
}

export async function analyzeCase(payload: AnalyzePayload): Promise<AnalyzeResponse> {
  const response = await fetch(`${API_URL}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || 'ไม่สามารถประเมินได้');
  }
  return response.json();
}

export async function fetchTrend(episodeId: number, metric: string): Promise<TrendResponse> {
  const response = await fetch(`${API_URL}/trend`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ episode_id: episodeId, metric }),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || 'ไม่สามารถดึงข้อมูลแนวโน้มได้');
  }
  return response.json();
}
