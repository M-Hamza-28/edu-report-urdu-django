// reporting-frontend/src/StudentList.js
import React, { useEffect, useState } from "react";
import API from "./api";

/**
 * StudentList
 * - Lists students
 * - Adds a new student (gender normalized to "Male"/"Female")
 * - Deletes a student (optional)
 * - Uses tutor dropdown if tutors endpoint is available
 *
 * Notes:
 * - Ensure backend Student.gender choices accept "Male" / "Female".
 * - If your backend also accepts "M"/"F", this file still normalizes to the full words.
 * - If you don't have /tutors/ endpoint yet, this will silently use the Tutor ID text input.
 */

function StudentList() {
  // Data
  const [students, setStudents] = useState([]);
  const [tutors, setTutors] = useState([]); // optional dropdown

  // Form fields
  const [fullName, setFullName] = useState("");
  const [tutor, setTutor] = useState("");
  const [gradeLevel, setGradeLevel] = useState("");
  const [gender, setGender] = useState(""); // should be "Male" or "Female"

  // UI state
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Fetch lists
  useEffect(() => {
    fetchStudents();
    // Try to load tutors; if it fails, we fall back to manual Tutor ID input
    API.get("tutors/")
      .then((res) => setTutors(res.data || []))
      .catch(() => setTutors([]));
  }, []);

  const fetchStudents = () => {
    API.get("students/")
      .then((res) => setStudents(res.data || []))
      .catch(() => setError("Failed to load students."));
  };

  // Small helper: collect readable error messages from DRF responses
  const extractApiError = (err) => {
    const data = err?.response?.data;
    if (!data) return "Check input/ID";

    // Preferred: field-level messages if present
    const parts = [];
    if (typeof data === "object") {
      Object.entries(data).forEach(([field, msg]) => {
        if (Array.isArray(msg)) {
          parts.push(`${field}: ${msg.join(", ")}`);
        } else if (typeof msg === "string") {
          parts.push(`${field}: ${msg}`);
        }
      });
    }

    // Fallback to detail or generic
    if (parts.length) return parts.join(" | ");
    return data.detail || "Check input/ID";
  };

  const handleAddStudent = (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    // Basic presence validation
    if (!fullName || !tutor || !gradeLevel || !gender) {
      setError("All fields are required.");
      return;
    }

    // Normalize gender just in case anything upstream sets "M"/"F"
    const normalizedGender =
      gender === "M" ? "Male" :
      gender === "F" ? "Female" :
      gender;

    // Coerce numeric fields properly
    const tutorId = Number(tutor);
    const grade = Number(gradeLevel);

    if (!Number.isInteger(tutorId) || tutorId <= 0) {
      setError("Tutor ID must be a valid number.");
      return;
    }
    if (!Number.isFinite(grade)) {
      setError("Grade Level must be a number.");
      return;
    }

    const payload = {
      full_name: fullName,
      tutor: tutorId,
      grade_level: grade,
      gender: normalizedGender, // <- always "Male"/"Female"
      registration_date: new Date().toISOString().slice(0, 10), // YYYY-MM-DD
    };

    // For quick debugging if needed:
    // console.log("Submitting payload:", payload);

    API.post("students/", payload)
      .then(() => {
        setSuccess("Student added!");
        setFullName(""); setTutor(""); setGradeLevel(""); setGender("");
        fetchStudents();
      })
      .catch((err) => {
        setError("Add failed: " + extractApiError(err));
      });
  };

  // Optional: delete a student
  const handleDeleteStudent = (id) => {
    if (!window.confirm(`Delete student #${id}?`)) return;
    setError(""); setSuccess("");
    API.delete(`students/${id}/`)
      .then(() => {
        setSuccess("Student deleted.");
        setStudents((prev) => prev.filter((s) => s.id !== id));
      })
      .catch((err) => setError("Delete failed: " + extractApiError(err)));
  };

  return (
    <div style={{ padding: 40, maxWidth: 640, margin: "auto" }}>
      <h2>Students</h2>

      {error && <div style={{ color: "red", marginBottom: 10 }}>{error}</div>}
      {success && <div style={{ color: "green", marginBottom: 10 }}>{success}</div>}

      <form onSubmit={handleAddStudent} style={{ marginBottom: 20, display: "flex", gap: 8, flexWrap: "wrap" }}>
        <input
          type="text"
          placeholder="Full Name"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          style={{ minWidth: 160 }}
          required
        />

        {/* Tutor selection: show dropdown if tutors are loaded, otherwise fallback to numeric input */}
        {tutors.length > 0 ? (
          <select
            value={tutor}
            onChange={(e) => setTutor(e.target.value)}
            style={{ minWidth: 160 }}
            required
          >
            <option value="">Select Tutor</option>
            {tutors.map((t) => (
              <option key={t.id} value={t.id}>{t.full_name} (#{t.id})</option>
            ))}
          </select>
        ) : (
          <input
            type="number"
            placeholder="Tutor ID"
            value={tutor}
            onChange={(e) => setTutor(e.target.value)}
            style={{ width: 120 }}
            required
          />
        )}

        <input
          type="number"
          placeholder="Grade Level"
          value={gradeLevel}
          onChange={(e) => setGradeLevel(e.target.value)}
          style={{ width: 120 }}
          required
        />

        <select
          value={gender}
          onChange={(e) => setGender(e.target.value)} // React uses camelCase
          style={{ minWidth: 160 }}
          required
        >
          <option value="">Select Gender</option>
          <option value="Male">Male</option>
          <option value="Female">Female</option>
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
            <th>Actions</th>{/* optional */}
          </tr>
        </thead>
        <tbody>
          {students.length === 0 ? (
            <tr>
              <td colSpan={6} style={{ textAlign: "center" }}>No students found</td>
            </tr>
          ) : (
            students.map((stu) => (
              <tr key={stu.id}>
                <td>{stu.id}</td>
                <td>{stu.full_name}</td>
                <td>{stu.tutor}</td>
                <td>{stu.grade_level}</td>
                <td>{stu.gender}</td>
                <td>
                  <button onClick={() => handleDeleteStudent(stu.id)}>Delete</button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

export default StudentList;
