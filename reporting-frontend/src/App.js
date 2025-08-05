// src/App.js
import React from "react";
import StudentList from "./StudentList";
import TutorList from "./TutorList";
import SubjectList from "./SubjectList";
import ExamList from "./ExamList";
import ReportForm from "./ReportForm";
import ReportList from "./ReportList";
import StudentProgressChart from "./StudentProgressChart";
import FeedbackForm from "./FeedbackForm";

function App() {
  return (
    <div>
      <StudentProgressChart />
      <ReportList />
      <ReportForm />
      <TutorList />
      <StudentList />
      <SubjectList />
      <ExamList />
      <FeedbackForm />
    </div>
  );
}

export default App;