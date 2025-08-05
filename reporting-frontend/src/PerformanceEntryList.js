import React, { useEffect, useState } from "react";
import API from "./api";

function PerformanceEntryList({ reportId }) {
  const [entries, setEntries] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (reportId) {
      setLoading(true);
      API.get(`entries/?report=${reportId}`)
        .then((res) => setEntries(res.data))
        .catch(() => setError("Failed to load entries."))
        .finally(() => setLoading(false));
    }
  }, [reportId]);

  if (!reportId) return null;

  return (
    <div style={{ marginTop: 24 }}>
      <h3>Performance Entries for Report #{reportId}</h3>
      {loading && <div>Loading...</div>}
      {error && <div style={{ color: "red" }}>{error}</div>}
      <table border={1} cellPadding={6} style={{ width: "100%", marginTop: 10 }}>
        <thead>
          <tr>
            <th>Subject</th>
            <th>Marks Obtained</th>
            <th>Total Marks</th>
          </tr>
        </thead>
        <tbody>
          {entries.length === 0 ? (
            <tr><td colSpan={3} style={{ textAlign: "center" }}>No entries found</td></tr>
          ) : (
            entries.map((e, idx) => (
              <tr key={e.id || idx}>
                <td>{e.subject_name || e.subject}</td>
                <td>{e.marks_obtained}</td>
                <td>{e.total_marks}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

export default PerformanceEntryList;
