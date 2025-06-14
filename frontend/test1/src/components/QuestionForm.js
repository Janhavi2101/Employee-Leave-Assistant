// QuestionForm.js
import React, { useState } from 'react';
import Select from 'react-select';

const QuestionForm = ({ employees, onAsk, onFileUpload }) => {
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [question, setQuestion] = useState('');
  const [empFile, setEmpFile] = useState(null);
  const [policyFile, setPolicyFile] = useState(null);

  const options = employees.map(name => ({ label: name, value: name }));

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!selectedEmployee || !question.trim()) return;
    onAsk(selectedEmployee.value, question.trim());
  };

  const handleUpload = async (e) => {
    e.preventDefault();

    if (!empFile || !policyFile) {
      alert("Please select both employee and policy files.");
      return;
    }

    const formData = new FormData();
    formData.append("emp_file", empFile);
    formData.append("policy_file", policyFile);

    try {
      const res = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      console.log("📦 Upload response:", data);

      if (data.message) {
        alert("✅ Files uploaded successfully!");
        if (onFileUpload) onFileUpload();  // Refresh employee dropdown
      } else {
        alert("❌ Upload failed: " + JSON.stringify(data));
      }
    } catch (error) {
      console.error("❌ Upload failed:", error);
      alert("Upload error occurred.");
    }
  };

  return (
    <div className="form">
      <form onSubmit={handleSubmit}>
        <label>Select or Search Employee:</label>
        <Select
          options={options}
          value={selectedEmployee}
          onChange={setSelectedEmployee}
          placeholder="Type to search..."
          isClearable
        />

        <label>Enter Question:</label>
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about leave, raise, task load, etc..."
          required
        />

        <button type="submit">Ask Assistant</button>
      </form>

      <form onSubmit={handleUpload} className="upload-form">
        <h3>Upload New Files</h3>

        <label>Employee Data (CSV/XLSX):</label>
        <input
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={(e) => setEmpFile(e.target.files[0])}
        />

        <label>Policy Document (PDF):</label>
        <input
          type="file"
          accept="application/pdf"
          onChange={(e) => setPolicyFile(e.target.files[0])}
        />

        <button type="submit">Upload Files</button>
      </form>
    </div>
  );
};

export default QuestionForm;
