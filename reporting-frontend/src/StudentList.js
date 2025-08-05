import React, { useEffect, useState } from "react";
import API from "./api";

function StudentList() {
  const [students, setStudents] = useState([]);
  const [fullName, setFullName] = useState("");
  const [tutor, setTutor] = useState("");
  const [gradeLevel, setGradeLevel] = useState("");
  const [gender, setGender] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Fetch all students
  useEffect(() => {
    fetchStudents();
  }, []);

  const fetchStudents = () => {
    API.get("students/")
      .then((res) => setStudents(res.data))
      .catch(() => setError("Failed to load students."));
  };

  const handleAddStudent = (e) => {
    e.preventDefault();
    setError(""); setSuccess("");
    if (!fullName || !tutor || !gradeLevel || !gender) {
      setError("All fields are required.");
      return;
    }
    API.post("students/", {
      full_name: fullName,
      tutor: tutor,
      grade_level: gradeLevel,
      gender: gender,
      registration_date: new Date().toISOString().slice(0, 10)
    })
      .then(() => {
        setSuccess("Student added!");
        setFullName(""); setTutor(""); setGradeLevel(""); setGender("");
        fetchStudents();
      })
      .catch((err) => setError("Add failed: " + (err.response?.data?.detail || "Check input/ID")));
  };

  return (
    <div style={{ padding: 40, maxWidth: 480, margin: "auto" }}>
      <h2>Students</h2>
      {error && <div style={{ color: "red" }}>{error}</div>}
      {success && <div style={{ color: "green" }}>{success}</div>}

      <form onSubmit={handleAddStudent} style={{ marginBottom: 20 }}>
        <input
          type="text"
          placeholder="Full Name"
          value={fullName}
          onChange={e => setFullName(e.target.value)}
          style={{ marginRight: 8 }}
        />
        <input
          type="number"
          placeholder="Tutor ID"
          value={tutor}
          onChange={e => setTutor(e.target.value)}
          style={{ marginRight: 8 }}
        />
        <input
          type="text"
          placeholder="Grade Level"
          value={gradeLevel}
          onChange={e => setGradeLevel(e.target.value)}
          style={{ marginRight: 8, width: 80 }}
        />
        <select
          value={gender}
          onChange={e => setGender(e.target.value)}
          style={{ marginRight: 8 }}
        >
          <option value="">Gender</option>
          <option value="M">Male</option>
          <option value="F">Female</option>
        </select>
        <button type="submit">Add Student</button>
      </form>

      <table border={1} cellPadding={6} style={{ width: "100%" }}>
        <thead>
          <tr>
            <th>ID</th>
            <th>Full Name</th>
            <th>Tutor ID</th>
            <th>Grade</th>
            <th>Gender</th>
          </tr>
        </thead>
        <tbody>
          {students.length === 0 ? (
            <tr><td colSpan={5} style={{ textAlign: "center" }}>No students found</td></tr>
          ) : (
            students.map(stu => (
              <tr key={stu.id}>
                <td>{stu.id}</td>
                <td>{stu.full_name}</td>
                <td>{stu.tutor}</td>
                <td>{stu.grade_level}</td>
                <td>{stu.gender}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

export default StudentList;
