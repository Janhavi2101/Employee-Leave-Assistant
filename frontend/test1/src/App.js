// App.js
import React, { useState, useEffect } from 'react';
import QuestionForm from './components/QuestionForm';
import './App.css';

const App = () => {
  const [response, setResponse] = useState('');
  const [employees, setEmployees] = useState([]);

  // Fetch employee names from backend
  const fetchEmployees = () => {
    fetch('http://localhost:8000/employees')
      .then(res => res.json())
      .then(data => {
        const sorted = data.sort((a, b) => a.localeCompare(b));
        setEmployees(sorted);
        console.log("✅ Loaded Employees:", sorted);
      })
      .catch(() => {
        console.error("❌ Failed to fetch employee list.");
        setEmployees([]);
      });
  };

  useEffect(() => {
    fetchEmployees();
  }, []);

  // Ask assistant a question
  const handleAsk = async (employee_name, question) => {
    try {
      const res = await fetch('http://localhost:8000/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ employee_name, question }),
      });
      const data = await res.json();
      setResponse(data.answer || 'No response received');
    } catch (error) {
      console.error("❌ Error asking question:", error);
      setResponse('Server error or connection failed.');
    }
  };

  return (
    <div className="container">
      <h1 className="title">Employee Assistant</h1>
      <QuestionForm
        onAsk={handleAsk}
        employees={employees}
        onFileUpload={fetchEmployees}
      />
      {response && (
        <div className="response">
          <strong>Assistant Response:</strong><br />
          {response}
        </div>
      )}
    </div>
  );
};

export default App;
