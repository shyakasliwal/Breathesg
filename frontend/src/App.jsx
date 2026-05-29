import { useEffect, useMemo, useState } from "react";
import { api } from "./api";

function isValidSession(data) {
  return Boolean(data?.user?.email);
}

const FILTERS = [
  { id: "all", label: "All rows" },
  { id: "pending", label: "Pending review", query: "?review_status=pending" },
  { id: "failed", label: "Failed parse", query: "?failed=true" },
  { id: "suspicious", label: "Suspicious", query: "?suspicious=true" },
];

export default function App() {
  const [session, setSession] = useState(null);
  const [email, setEmail] = useState("analyst@demo.local");
  const [password, setPassword] = useState("demo12345");
  const [error, setError] = useState("");
  const [dashboard, setDashboard] = useState(null);
  const [records, setRecords] = useState([]);
  const [filter, setFilter] = useState("pending");
  const [busy, setBusy] = useState(false);

  const activeFilter = useMemo(() => FILTERS.find((f) => f.id === filter) || FILTERS[0], [filter]);

  async function refresh() {
    const [dash, recs] = await Promise.all([
      api.dashboard(),
      api.records(activeFilter.query || ""),
    ]);
    setDashboard(dash);
    setRecords(recs);
  }

  useEffect(() => {
    api
      .me()
      .then((data) => {
        if (!isValidSession(data)) {
          setSession(null);
          return;
        }
        setSession(data);
        return refresh();
      })
      .catch(() => setSession(null));
  }, []);

  useEffect(() => {
    if (session) refresh().catch((err) => setError(err.message));
  }, [filter, session]);

  async function handleLogin(event) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      await api.login(email, password);
      const me = await api.me();
      if (!isValidSession(me)) {
        throw new Error("Login succeeded but session was not established.");
      }
      setSession(me);
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleUpload(sourceType, event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      await api.ingest(sourceType, file);
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
      event.target.value = "";
    }
  }

  async function handleReview(id, action) {
    setBusy(true);
    setError("");
    try {
      await api.review(id, action);
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (!isValidSession(session)) {
    return (
      <div className="page center">
        <form className="card login" onSubmit={handleLogin}>
          <h1>Breathe ESG Analyst Review</h1>
          <p>Sign in to review ingested activity data before audit lock.</p>
          <label>
            Email
            <input value={email} onChange={(e) => setEmail(e.target.value)} />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </label>
          {error && <p className="error">{error}</p>}
          <button disabled={busy}>{busy ? "Signing in..." : "Sign in"}</button>
        </form>
      </div>
    );
  }

  return (
    <div className="page">
      <header className="topbar">
        <div>
          <h1>Review dashboard</h1>
          <p>
            {session.organization?.name} · {session.user?.email}
          </p>
        </div>
        <button
          className="ghost"
          onClick={async () => {
            await api.logout();
            setSession(null);
          }}
        >
          Log out
        </button>
      </header>

      {error && <p className="error banner">{error}</p>}

      {dashboard && (
        <section className="stats">
          <Stat label="Total rows" value={dashboard.totals.records} />
          <Stat label="Failed parse" value={dashboard.totals.failed} tone="bad" />
          <Stat label="Suspicious" value={dashboard.totals.suspicious} tone="warn" />
          <Stat label="Pending review" value={dashboard.totals.pending_review} />
          <Stat label="Approved (locked)" value={dashboard.totals.approved_locked} tone="good" />
        </section>
      )}

      <section className="card uploads">
        <h2>Upload new file</h2>
        <div className="upload-grid">
          <UploadTile label="SAP export" source="sap" onChange={handleUpload} disabled={busy} />
          <UploadTile label="Utility CSV" source="utility" onChange={handleUpload} disabled={busy} />
          <UploadTile label="Travel export" source="travel" onChange={handleUpload} disabled={busy} />
        </div>
      </section>

      <section className="card">
        <div className="row between">
          <h2>Activity records</h2>
          <div className="chips">
            {FILTERS.map((f) => (
              <button
                key={f.id}
                className={filter === f.id ? "chip active" : "chip"}
                onClick={() => setFilter(f.id)}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Source</th>
                <th>Scope</th>
                <th>Category</th>
                <th>Date / period</th>
                <th>Normalized</th>
                <th>Flags</th>
                <th>Status</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {records.map((row) => (
                <tr key={row.id} className={!row.parse_ok ? "row-failed" : row.suspicious ? "row-warn" : ""}>
                  <td>{row.source_type}</td>
                  <td>{row.scope}</td>
                  <td>{row.category}</td>
                  <td>
                    {row.activity_date || "-"}
                    {row.period_start ? (
                      <div className="muted">
                        {row.period_start} → {row.period_end}
                      </div>
                    ) : null}
                  </td>
                  <td>
                    {row.normalized_quantity ?? row.quantity ?? "-"} {row.normalized_unit || row.unit}
                  </td>
                  <td>
                    {(row.validation_flags || []).join(", ") || "—"}
                  </td>
                  <td>
                    {row.review_status}
                    {row.is_locked_for_audit ? " (locked)" : ""}
                  </td>
                  <td className="actions">
                    {row.review_status === "pending" && row.parse_ok && (
                      <>
                        <button onClick={() => handleReview(row.id, "approve")} disabled={busy}>
                          Approve
                        </button>
                        <button className="ghost" onClick={() => handleReview(row.id, "reject")} disabled={busy}>
                          Reject
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
              {!records.length && (
                <tr>
                  <td colSpan="8">No records for this filter.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function Stat({ label, value, tone }) {
  return (
    <div className={`stat ${tone || ""}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function UploadTile({ label, source, onChange, disabled }) {
  return (
    <label className="upload-tile">
      <span>{label}</span>
      <input type="file" accept=".csv" disabled={disabled} onChange={(e) => onChange(source, e)} />
    </label>
  );
}
