import React, { useEffect, useState } from "react";
import API from "./api";

function ExamList() {
  const [exams, setExams] = useState([]);
  const [examType, setExamType] = useState("");
  const [name, setName] = useState("");
  const [date, setDate] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    fetchExams();
  }, []);

  const fetchExams = () => {
    API.get("exams/")
      .then((res) => setExams(res.data))
      .catch(() => setError("Failed to load exams."));
  };

  const handleAddExam = (e) => {
    e.preventDefault();
    setError(""); setSuccess("");
    if (!name || !date) {
      setError("All fields required.");
      return;
    }
    API.post("exams/", { name, exam_type: examType, date })
      .then(() => {
        setSuccess("Exam added!");
        setName(""); setDate("");
        fetchExams();
      })
      .catch((err) => setError("Add failed: " + (err.response?.data?.detail || "Check input")));
  };

  return (
    <div style={{ padding: 40, maxWidth: 480, margin: "auto" }}>
      <h2>Exams</h2>
      {error && <div style={{ color: "red" }}>{error}</div>}
      {success && <div style={{ color: "green" }}>{success}</div>}

      <form onSubmit={handleAddExam} style={{ marginBottom: 20 }}>
        <input
          type="text"
          placeholder="Exam Name"
          value={name}
          onChange={e => setName(e.target.value)}
          style={{ marginRight: 8 }}
        />
        <input
          type="text"
          placeholder="Exam Type"
          value={examType}
          onChange={e => setExamType(e.target.value)}
          style={{ marginRight: 8 }}
        />
        <input
          type="date"
          placeholder="Date"
          value={date}
          onChange={e => setDate(e.target.value)}
          style={{ marginRight: 8 }}
        />
        <button type="submit">Add Exam</button>
      </form>

      <table border={1} cellPadding={6} style={{ width: "100%" }}>
        <thead>
          <tr>
            <th>ID</th>
            <th>Exam Name</th>
            <th>Date</th>
          </tr>
        </thead>
        <tbody>
          {exams.length === 0 ? (
            <tr><td colSpan={3} style={{ textAlign: "center" }}>No exams found</td></tr>
          ) : (
            exams.map(exam => (
              <tr key={exam.id}>
                <td>{exam.id}</td>
                <td>{exam.name}</td>
                <td>{exam.date}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

export default ExamList;
