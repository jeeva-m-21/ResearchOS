const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init)
  if (!res.ok) throw new Error(`API ${res.status}`)
  return res.json() as Promise<T>
}
