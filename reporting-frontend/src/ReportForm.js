import React, { useEffect, useState } from "react";
import API from "./api";

function ReportForm() {
  // Dropdown options
  const [students, setStudents] = useState([]);
  const [tutors, setTutors] = useState([]);
  const [exams, setExams] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [performanceEntries, setPerformanceEntries] = useState([
    { subject: "", marks_obtained: "", total_marks: "" }
  ]);
  const [student, setStudent] = useState("");
  const [tutor, setTutor] = useState("");
  const [exam, setExam] = useState("");
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  // Fetch all selectable data on mount
  useEffect(() => {
    API.get("students/").then(r => setStudents(r.data));
    API.get("tutors/").then(r => setTutors(r.data));
    API.get("exams/").then(r => setExams(r.data));
    API.get("subjects/").then(r => setSubjects(r.data));
  }, []);

  // Refresh exams for dropdown
  const reloadExams = () => {
    API.get("exams/").then(r => setExams(r.data));
  };

  // Handle adding/removing rows for multiple subjects
  const addEntry = () => {
    setPerformanceEntries([...performanceEntries, { subject: "", marks_obtained: "", total_marks: "" }]);
  };

  const removeEntry = idx => {
    if (performanceEntries.length === 1) return;
    setPerformanceEntries(performanceEntries.filter((_, i) => i !== idx));
  };

  const updateEntry = (idx, field, value) => {
    const entries = performanceEntries.map((entry, i) =>
      i === idx ? { ...entry, [field]: value } : entry
    );
    setPerformanceEntries(entries);
  };

  // Handle submit
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(""); setSuccess("");
    if (!student || !tutor || !exam) {
      setError("Student, Tutor, and Exam are required.");
      return;
    }
    if (performanceEntries.some(entry =>
      !entry.subject || !entry.marks_obtained || !entry.total_marks
    )) {
      setError("All performance entry fields are required.");
      return;
    }
  // 🚨 Check for duplicate subjects
  const seenSubjects = new Set();
    for (let entry of performanceEntries) {
      if (seenSubjects.has(entry.subject)) {
        setError("Duplicate subject for the same report is not allowed.");
        return;
      }
      seenSubjects.add(entry.subject);
    }
    try {
      // Create report
      const reportResp = await API.post("reports/", {
        student, tutor, exam
      });
      const reportId = reportResp.data.id;
      // Create entries
      await Promise.all(performanceEntries.map(entry =>
        API.post("entries/", {
          report: reportId,
          subject: entry.subject,
          marks_obtained: entry.marks_obtained,
          total_marks: entry.total_marks
        })
      ));
      setSuccess("Report and entries added!");
      setStudent(""); setTutor(""); setExam("");
      setPerformanceEntries([{ subject: "", marks_obtained: "", total_marks: "" }]);
    } catch (err) {
      setError("Failed to create report/entries: " + (err.response?.data?.detail || "Check input"));
    }
  };

  return (
    <div style={{ padding: 40, maxWidth: 720, margin: "auto" }}>
      <h2>Create Report & Performance Entries</h2>
      {error && <div style={{ color: "red" }}>{error}</div>}
      {success && <div style={{ color: "green" }}>{success}</div>}

      <form onSubmit={handleSubmit}>
        <label>
          Student:
          <select value={student} onChange={e => setStudent(e.target.value)} required>
            <option value="">Select</option>
            {students.map(stu => (
              <option key={stu.id} value={stu.id}>{stu.full_name}</option>
            ))}
          </select>
        </label>
        <label style={{ marginLeft: 16 }}>
          Tutor:
          <select value={tutor} onChange={e => setTutor(e.target.value)} required>
            <option value="">Select</option>
            {tutors.map(tut => (
              <option key={tut.id} value={tut.id}>{tut.full_name}</option>
            ))}
          </select>
        </label>
        <label style={{ marginLeft: 16 }}>
          Exam:
          <select value={exam} onChange={e => setExam(e.target.value)} required>
            <option value="">Select</option>
            {exams.map(ex => (
              <option key={ex.id} value={ex.id}>
                {ex.name} ({ex.exam_type}) {ex.date}
              </option>
            ))}
          </select>
          {/* Refresh Exams Button */}
          <button
            type="button"
            onClick={reloadExams}
            style={{
              marginLeft: 8,
              padding: "2px 10px",
              cursor: "pointer"
            }}
            title="Reload exam list"
          >⟳</button>
        </label>

        <div style={{ marginTop: 20 }}>
          <b>Performance Entries</b>
          {performanceEntries.map((entry, idx) => (
            <div key={idx} style={{ marginBottom: 8 }}>
              <select
                value={entry.subject}
                onChange={e => updateEntry(idx, "subject", e.target.value)}
                style={{ marginRight: 8 }}
                required
              >
                <option value="">Subject</option>
                {subjects.map(sub => (
                  <option key={sub.id} value={sub.id}>{sub.name}</option>
                ))}
              </select>
              <input
                type="number"
                placeholder="Marks Obtained"
                value={entry.marks_obtained}
                onChange={e => updateEntry(idx, "marks_obtained", e.target.value)}
                style={{ marginRight: 8, width: 110 }}
                required
              />
              <input
                type="number"
                placeholder="Total Marks"
                value={entry.total_marks}
                onChange={e => updateEntry(idx, "total_marks", e.target.value)}
                style={{ marginRight: 8, width: 100 }}
                required
              />
              <button type="button" onClick={() => removeEntry(idx)} disabled={performanceEntries.length === 1}>
                Remove
              </button>
            </div>
          ))}
          <button type="button" onClick={addEntry} style={{ marginTop: 4 }}>
            Add Subject Entry
          </button>
        </div>
        <br />
        <button type="submit" style={{ marginTop: 12 }}>Create Report</button>
      </form>
    </div>
  );
}

export default ReportForm;
