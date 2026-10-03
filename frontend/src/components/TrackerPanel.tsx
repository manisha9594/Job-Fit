import { useEffect, useState } from "react";
import { api } from "../api";
import { STATUSES, type Application } from "../types";

export default function TrackerPanel() {
  const [apps, setApps] = useState<Application[]>([]);
  const [due, setDue] = useState<Application[]>([]);
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [url, setUrl] = useState("");
  const [location, setLocation] = useState("");

  async function refresh() {
    const [list, followups] = await Promise.all([
      api.trackerList(),
      api.followups(),
    ]);
    setApps(list.applications);
    setDue(followups.due);
  }

  useEffect(() => {
    refresh().catch(() => {});
  }, []);

  async function add() {
    if (!company.trim() || !role.trim()) return;
    await api.trackerAdd({ company, role, url, location });
    setCompany("");
    setRole("");
    setUrl("");
    setLocation("");
    await refresh();
  }

  return (
    <div>
      <h2>Application tracker</h2>
      <div className="card">
        <h4>Log an application</h4>
        <div className="row">
          <input placeholder="Company" value={company} onChange={(e) => setCompany(e.target.value)} />
          <input placeholder="Role" value={role} onChange={(e) => setRole(e.target.value)} />
        </div>
        <div className="row">
          <input placeholder="Job URL" value={url} onChange={(e) => setUrl(e.target.value)} />
          <input placeholder="Location" value={location} onChange={(e) => setLocation(e.target.value)} />
          <button onClick={add}>Add</button>
        </div>
      </div>
      {due.length > 0 && (
        <div className="card warn">
          <h4>⏰ Follow-ups due ({due.length})</h4>
          <ul>
            {due.map((a) => (
              <li key={a.id}>
                {a.company} — {a.role} (applied {a.date_applied})
              </li>
            ))}
          </ul>
        </div>
      )}
      <table>
        <thead>
          <tr>
            <th>Company</th>
            <th>Role</th>
            <th>Applied</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {apps.map((a) => (
            <tr key={a.id}>
              <td>{a.url ? <a href={a.url} target="_blank" rel="noreferrer">{a.company}</a> : a.company}</td>
              <td>{a.role}</td>
              <td>{a.date_applied}</td>
              <td>
                <select
                  value={a.status}
                  onChange={async (e) => {
                    await api.trackerUpdate(a.id, e.target.value);
                    await refresh();
                  }}
                >
                  {STATUSES.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </td>
              <td>
                <button
                  className="danger"
                  onClick={async () => {
                    await api.trackerDelete(a.id);
                    await refresh();
                  }}
                >
                  ✕
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {apps.length === 0 && <p className="muted">No applications logged yet.</p>}
    </div>
  );
}
