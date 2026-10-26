export async function api(path, params = {}) {
  const qs = new URLSearchParams(params).toString();
  const r = await fetch(`/api/${path}?${qs}`);
  if (!r.ok) {
    const j = await r.json().catch(() => ({}));
    throw new Error(j.detail || `Request failed (${r.status})`);
  }
  return r.json();
}
export const fmt = (n, d = 0) => (n == null ? "n/a" : Number(n).toLocaleString("en-GB", { maximumFractionDigits: d }));
