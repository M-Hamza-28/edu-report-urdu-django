import React, { useEffect, useState } from "react";
import API from "./api";
import { Line } from "react-chartjs-2";
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

function StudentProgressChart() {
  const [students, setStudents] = useState([]);
  const [selectedStudent, setSelectedStudent] = useState("");
  const [chartData, setChartData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    API.get("students/")
      .then(res => setStudents(res.data))
      .catch(() => setError("Could not load students"));
  }, []);

  useEffect(() => {
    if (!selectedStudent) return;
    API.get(`reports/student_progress/${selectedStudent}/`)
      .then(res => {
        const data = res.data; // { subject: [ {exam, marks_obtained, total_marks, percentage}, ...], ... }
        // Prepare chart datasets
        const examsSet = new Set();
        Object.values(data).forEach(arr => arr.forEach(entry => examsSet.add(entry.exam)));
        const exams = Array.from(examsSet);
        const datasets = Object.keys(data).map(subject => ({
          label: subject,
          data: exams.map(exam => {
            const entry = data[subject].find(e => e.exam === exam);
            return entry ? entry.percentage : null;
          }),
          fill: false,
          tension: 0.3,
        }));
        setChartData({
          labels: exams,
          datasets,
        });
      })
      .catch(() => setError("Could not load chart data"));
  }, [selectedStudent]);

  return (
    <div style={{ padding: 40, maxWidth: 900, margin: "auto" }}>
      <h2>Student Progress Chart</h2>
      {error && <div style={{ color: "red" }}>{error}</div>}
      <select
        value={selectedStudent}
        onChange={e => setSelectedStudent(e.target.value)}
        style={{ marginBottom: 16 }}
      >
        <option value="">Select Student</option>
        {students.map(stu => (
          <option key={stu.id} value={stu.id}>{stu.full_name}</option>
        ))}
      </select>
      {chartData && (
        <Line
          data={chartData}
          options={{
            responsive: true,
            plugins: {
              legend: { position: 'bottom' },
              title: { display: true, text: 'Performance by Subject and Exam (%)' },
            },
            scales: {
              y: {
                title: { display: true, text: 'Percentage' },
                min: 0, max: 100,
              }
            }
          }}
        />
      )}
    </div>
  );
}

export default StudentProgressChart;
