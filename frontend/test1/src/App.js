import React, { useState, useEffect } from 'react';
import QuestionForm from './components/QuestionForm';
import { Users, CheckCircle } from 'lucide-react';
import './App.css';

const App = () => {
  const [response, setResponse] = useState('');
  const [employees, setEmployees] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

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

  const handleAsk = async (employee_name, question) => {
    setIsLoading(true);
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
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <div className="container">
        {/* Header */}
        <div className="header">
          <div className="header-icon">
            <Users className="header-icon-svg" />
          </div>
          <h1 className="title">Employee Assistant</h1>
          <p className="subtitle">
            Upload employee data and ask intelligent questions about your workforce
          </p>
        </div>

        {/* Main Content */}
        <div className="main-content">
          <QuestionForm
            onAsk={handleAsk}
            employees={employees}
            onFileUpload={fetchEmployees}
          />

          {/* Response Section */}
          {(response || isLoading) && (
            <div className="response-section">
              <div className="response-header">
                <div className="response-icon">
                  {isLoading ? (
                    <div className="loading-spinner"></div>
                  ) : (
                    <CheckCircle className="response-icon-svg" />
                  )}
                </div>
                <h3 className="response-title">
                  {isLoading ? 'Processing...' : 'Assistant Response'}
                </h3>
              </div>
              
              {isLoading ? (
                <div className="loading-content">
                  <div className="loading-spinner small"></div>
                  <span>Analyzing your question...</span>
                </div>
              ) : (
                <div className="response-content">
                  <p className="response-text">
                    {response}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default App;