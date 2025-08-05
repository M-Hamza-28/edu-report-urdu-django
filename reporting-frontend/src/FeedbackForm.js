import React, { useState } from "react";
import API from "./api";

function FeedbackForm() {
  const [name, setName] = useState("");
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!message) {
      setStatus("Please enter your feedback.");
      return;
    }
    API.post("feedback/", { name, message })
      .then(() => {
        setStatus("Thank you for your feedback!");
        setName(""); setMessage("");
      })
      .catch(() => setStatus("Error sending feedback."));
  };

  return (
    <div style={{ padding: 40, maxWidth: 400, margin: "auto" }}>
      <h2>Feedback</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Your Name (optional)"
          value={name}
          onChange={e => setName(e.target.value)}
          style={{ marginBottom: 8, width: "100%" }}
        />
        <textarea
          placeholder="Your feedback..."
          value={message}
          onChange={e => setMessage(e.target.value)}
          rows={4}
          style={{ width: "100%" }}
        />
        <button type="submit" style={{ marginTop: 8 }}>Send</button>
      </form>
      {status && <div style={{ marginTop: 8, color: "green" }}>{status}</div>}
    </div>
  );
}

export default FeedbackForm;
