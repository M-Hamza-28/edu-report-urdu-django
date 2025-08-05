import React, { useEffect, useState } from "react";
import API from "./api";
import PerformanceEntryList from "./PerformanceEntryList";

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

  // PDF download handler
  const handleDownloadPDF = (reportId) => {
    API.get(`reports/${reportId}/generate_pdf/` ,{ responseType: 'blob' })

      .then((res) => {
        // Create a link to download the PDF blob
        const url = window.URL.createObjectURL(new Blob([res.data], { type: "application/pdf" }));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `report_${reportId}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.remove();
      })
      .catch(() => alert("PDF download failed"));
  };

  // const handleSendReport = (reportId, method) => {
  // API.post(`reports/${reportId}/send_report/`, { method })
  //   .then(res => alert(`Report sent: ${res.data.status}`))
  //   .catch(() => alert("Sending failed"));
  // };


  return (
    <div style={{ padding: 40, maxWidth: 900, margin: "auto" }}>
      <h2>All Reports</h2>
      {loading && <div>Loading...</div>}
      {error && <div style={{ color: "red" }}>{error}</div>}
      <table border={1} cellPadding={6} style={{ width: "100%" }}>
        <thead>
          <tr>
            <th>ID</th>
            <th>Student</th>
            <th>Tutor</th>
            <th>Exam</th>
            <th>Date</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {reports.length === 0 ? (
            <tr><td colSpan={6} style={{ textAlign: "center" }}>No reports found</td></tr>
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
                  <button onClick={() => handleDownloadPDF(r.id)} style={{ marginLeft: 6 }}>Download PDF</button>
                  {/* <button onClick={() => handleSendReport(r.id, 'whatsapp')} style={{ marginLeft: 6 }}>Send WhatsApp</button>
                  <button onClick={() => handleSendReport(r.id, 'sms')} style={{ marginLeft: 6 }}>Send SMS</button>
                  <button onClick={() => handleSendReport(r.id, 'email')} style={{ marginLeft: 6 }}>Send Email</button> */}
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
