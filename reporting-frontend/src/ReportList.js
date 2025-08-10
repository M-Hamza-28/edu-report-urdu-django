// reporting-frontend/src/ReportList.js
import React, { useEffect, useState } from "react";
import API from "./api";
import PerformanceEntryList from "./PerformanceEntryList";

/**
 * Small inline component to handle language selection + download
 * Assumes your backend endpoint supports: /reports/<id>/generate_pdf/?lang=en|ur
 * If your route is different, adjust the URL below in `handleDownload`.
 */
function DownloadMenu({ reportId }) {
  const [lang, setLang] = useState("");            // "en" | "ur"
  const [downloading, setDownloading] = useState(false);

  const handleDownload = async () => {
    if (!lang) {
      alert("براہ کرم زبان منتخب کریں / Please select a language first");
      return;
    }
    try {
      setDownloading(true);
      const res = await API.get(`reports/${reportId}/generate_pdf/`, {
        params: { lang },                          // <-- ?lang=en or ur
        responseType: "blob",
      });

      // Build a downloadable Blob -> <a download=...>
      const blob = new Blob([res.data], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `report_${reportId}_${lang}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      console.error(e);
      alert("PDF download failed");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <span style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
      <select
        value={lang}
        onChange={(e) => setLang(e.target.value)}
        aria-label="Language"
      >
        <option value="">{/* placeholder */}Language / زبان</option>
        <option value="en">English</option>
        <option value="ur">اردو</option>
      </select>
      <button
        type="button"
        onClick={handleDownload}
        disabled={downloading}
      >
        {downloading ? "Downloading..." : "Download"}
      </button>
    </span>
  );
}

function ReportList() {
  const [reports, setReports] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [selectedReport, setSelectedReport] = useState(null);

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = () => {
    setLoading(true);
    API.get("reports/")
      .then((res) => setReports(res.data))
      .catch(() => setError("Failed to load reports."))
      .finally(() => setLoading(false));
  };

  // Kept for reference; not used now that per-row DownloadMenu is present.
  const handleDownloadPDF = (reportId) => {
    API.get(`reports/${reportId}/generate_pdf/`, { responseType: "blob" })
      .then((res) => {
        const url = window.URL.createObjectURL(new Blob([res.data], { type: "application/pdf" }));
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", `report_${reportId}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      })
      .catch(() => alert("PDF download failed"));
  };

  return (
    <div style={{ padding: 40, maxWidth: 900, margin: "auto" }}>
      <h2>All Reports</h2>
      {loading && <div>Loading...</div>}
      {error && <div style={{ color: "red" }}>{error}</div>}

      <table border={1} cellPadding={6} style={{ width: "100%" }}>
        <thead>
          <tr>
            <th>Actions (Lang)</th>
            <th>ID</th>
            <th>Student</th>
            <th>Tutor</th>
            <th>Exam</th>
            <th>Date</th>
            <th>Actions</th> {/* includes Language dropdown + Download */}
          </tr>
        </thead>
        <tbody>
          {reports.length === 0 ? (
            <tr>
              <td colSpan={6} style={{ textAlign: "center" }}>No reports found</td>
            </tr>
          ) : (
            reports.map((r) => (
              <tr key={r.id}>
                <td>{r.id}</td>
                <td>{r.student?.full_name || r.student}</td>
                <td>{r.tutor?.full_name || r.tutor}</td>
                <td>{r.exam?.name || r.exam}</td>
                <td>{r.exam?.date || ""}</td>
                <td>
                  <button onClick={() => setSelectedReport(r.id)}>View Entries</button>
                  {/* Old single-language download:
                  <button onClick={() => handleDownloadPDF(r.id)} style={{ marginLeft: 6 }}>Download PDF</button> */}
                  <span style={{ marginLeft: 8 }}>
                    <DownloadMenu reportId={r.id} />
                  </span>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>

      <button onClick={fetchReports} style={{ marginTop: 12 }}>Refresh Reports</button>

      {/* Show performance entries for the selected report */}
      {selectedReport && (
        <PerformanceEntryList reportId={selectedReport} />
      )}
    </div>
  );
}

export default ReportList;
