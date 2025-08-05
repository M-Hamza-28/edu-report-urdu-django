import React, { useEffect, useState } from "react";
import API from "./api";

function TutorList() {
  const [tutors, setTutors] = useState([]);
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    fetchTutors();
  }, []);

  const fetchTutors = () => {
    API.get("tutors/")
      .then((res) => setTutors(res.data))
      .catch(() => setError("Failed to load tutors."));
  };

  const handleAddTutor = (e) => {
    e.preventDefault();
    setError(""); setSuccess("");
    if (!fullName || !phone) {
      setError("Both fields required.");
      return;
    }
    API.post("tutors/", {
      full_name: fullName,
      phone: phone,
      // Add other fields as needed by your Tutor model
    })
      .then(() => {
        setSuccess("Tutor added!");
        setFullName(""); setPhone("");
        fetchTutors();
      })
      .catch((err) => setError("Add failed: " + (err.response?.data?.detail || "Check input")));
  };

  return (
    <div style={{ padding: 40, maxWidth: 480, margin: "auto" }}>
      <h2>Tutors</h2>
      {error && <div style={{ color: "red" }}>{error}</div>}
      {success && <div style={{ color: "green" }}>{success}</div>}

      <form onSubmit={handleAddTutor} style={{ marginBottom: 20 }}>
        <input
          type="text"
          placeholder="Full Name"
          value={fullName}
          onChange={e => setFullName(e.target.value)}
          style={{ marginRight: 8 }}
        />
        <input
          type="text"
          placeholder="Phone"
          value={phone}
          onChange={e => setPhone(e.target.value)}
          style={{ marginRight: 8 }}
        />
        <button type="submit">Add Tutor</button>
      </form>

      <table border={1} cellPadding={6} style={{ width: "100%" }}>
        <thead>
          <tr>
            <th>ID</th>
            <th>Full Name</th>
            <th>Phone</th>
          </tr>
        </thead>
        <tbody>
          {tutors.length === 0 ? (
            <tr><td colSpan={3} style={{ textAlign: "center" }}>No tutors found</td></tr>
          ) : (
            tutors.map(tut => (
              <tr key={tut.id}>
                <td>{tut.id}</td>
                <td>{tut.full_name}</td>
                <td>{tut.phone}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

export default TutorList;
