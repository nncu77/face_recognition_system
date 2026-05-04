const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ---- Response types (mirror FastAPI app/main.py) ----

export type RegisterResponse = {
  user_id: string;
  name: string;
  message: string;
};

export type RecognizeResponse = {
  matched: boolean;
  user_id: string | null;
  name: string | null;
  similarity: number;
  is_live: boolean;
  bbox: [number, number, number, number] | null;   // [x1, y1, x2, y2]
  det_score: number;
};

export type UserInfo = {
  user_id: string;
  name: string;
  created_at: string | null;
};

export type LogEntry = {
  user_id: string | null;
  name: string | null;
  similarity: number;
  timestamp: string;
  is_live: boolean;
};

export type LivenessResponse = {
  is_live: boolean;
  blink_count: number;
  required_blinks: number;
  frames_processed: number;
  frames_with_face: number;
  ear_history: number[];
};

// ---- API client ----

async function jsonFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, init);
  if (!res.ok) {
    let detail: string;
    try {
      const body = await res.json();
      detail = body.detail ?? JSON.stringify(body);
    } catch {
      detail = await res.text();
    }
    throw new Error(`${res.status} ${res.statusText}: ${detail}`);
  }
  return res.json();
}

export function registerUser(
  name: string,
  image: File,
): Promise<RegisterResponse> {
  const fd = new FormData();
  fd.append("name", name);
  fd.append("image", image);
  return jsonFetch<RegisterResponse>("/api/register", {
    method: "POST",
    body: fd,
  });
}

export function recognize(
  image: File,
  isLive = false,
): Promise<RecognizeResponse> {
  const fd = new FormData();
  fd.append("image", image);
  fd.append("is_live", String(isLive));
  return jsonFetch<RecognizeResponse>("/api/recognize", {
    method: "POST",
    body: fd,
  });
}

export function listUsers(): Promise<UserInfo[]> {
  return jsonFetch<UserInfo[]>("/api/users");
}

export function deleteUser(userId: string): Promise<{ message: string }> {
  return jsonFetch<{ message: string }>(`/api/users/${userId}`, {
    method: "DELETE",
  });
}

export function listLogs(limit = 50): Promise<LogEntry[]> {
  return jsonFetch<LogEntry[]>(`/api/logs?limit=${limit}`);
}

export { API_URL };
