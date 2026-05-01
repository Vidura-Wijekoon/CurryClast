export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="loading">
      <div className="spinner" />
      <span>{label}</span>
    </div>
  );
}

export function ErrorBox({ error }: { error: unknown }) {
  const msg = error instanceof Error ? error.message : String(error);
  return (
    <div className="error">
      <strong>Something went wrong.</strong>
      <div style={{ marginTop: 6, fontSize: 13, opacity: 0.9 }}>{msg}</div>
      <div style={{ marginTop: 10, fontSize: 12, opacity: 0.7 }}>
        Make sure the FastAPI backend is running:{" "}
        <code>uvicorn src.api.service:app --reload</code>
      </div>
    </div>
  );
}
