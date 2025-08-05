import React, { useEffect, useState } from "react";
import API from "./api";

function SubjectList() {
  const [subjects, setSubjects] = useState([]);
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    fetchSubjects();
  }, []);

  const fetchSubjects = () => {
    API.get("subjects/")
      .then((res) => setSubjects(res.data))
      .catch(() => setError("Failed to load subjects."));
  };

  const handleAddSubject = (e) => {
    e.preventDefault();
    setError(""); setSuccess("");
    if (!name) {
      setError("Subject name required.");
      return;
    }
    API.post("subjects/", { name })
      .then(() => {
        setSuccess("Subject added!");
        setName("");
        fetchSubjects();
      })
      .catch((err) => setError("Add failed: " + (err.response?.data?.detail || "Check input")));
  };

  return (
    <div style={{ padding: 40, maxWidth: 480, margin: "auto" }}>
      <h2>Subjects</h2>
      {error && <div style={{ color: "red" }}>{error}</div>}
      {success && <div style={{ color: "green" }}>{success}</div>}

      <form onSubmit={handleAddSubject} style={{ marginBottom: 20 }}>
        <input
          type="text"
          placeholder="Subject Name"
          value={name}
          onChange={e => setName(e.target.value)}
          style={{ marginRight: 8 }}
        />
        <button type="submit">Add Subject</button>
      </form>

      <table border={1} cellPadding={6} style={{ width: "100%" }}>
        <thead>
          <tr>
            <th>ID</th>
            <th>Subject Name</th>
          </tr>
        </thead>
        <tbody>
          {subjects.length === 0 ? (
            <tr><td colSpan={2} style={{ textAlign: "center" }}>No subjects found</td></tr>
          ) : (
            subjects.map(sub => (
              <tr key={sub.id}>
                <td>{sub.id}</td>
                <td>{sub.name}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

export default SubjectList;
