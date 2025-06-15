import React, { useState } from 'react';
import { Upload, MessageSquare, Users, FileText, Search, CheckCircle } from 'lucide-react';

const QuestionForm = ({ employees, onAsk, onFileUpload }) => {
  const [selectedEmployee, setSelectedEmployee] = useState('');
  const [question, setQuestion] = useState('');
  const [empFile, setEmpFile] = useState(null);
  const [policyFile, setPolicyFile] = useState(null);
  const [lastUploadedEmpFile, setLastUploadedEmpFile] = useState(null);
  const [lastUploadedPolicyFile, setLastUploadedPolicyFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);

  const filteredEmployees = (employees || []).filter(name => 
    name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (!selectedEmployee || !question.trim()) return;
    onAsk(selectedEmployee, question.trim());
  };

  const clearQuestion = () => {
    setQuestion('');
  };

  const handleUpload = async (e) => {
    if (e) e.preventDefault();
    if (!empFile || !policyFile) {
      alert("Please select both employee and policy files.");
      return;
    }

    setIsUploading(true);
    const formData = new FormData();
    formData.append("emp_file", empFile);
    formData.append("policy_file", policyFile);

    try {
      const res = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      if (data.message) {
        alert("✅ Files uploaded successfully!");
        if (onFileUpload) onFileUpload();

        // Save uploaded filenames
        setLastUploadedEmpFile(empFile.name);
        setLastUploadedPolicyFile(policyFile.name);

        // Clear file inputs and state
        setEmpFile(null);
        setPolicyFile(null);
        document.getElementById('emp-file-input').value = '';
        document.getElementById('policy-file-input').value = '';
      } else {
        alert("❌ Upload failed: " + JSON.stringify(data));
      }
    } catch (error) {
      console.error("❌ Upload failed:", error);
      alert("Upload error occurred.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleEmployeeSelect = (employee) => {
    setSelectedEmployee(employee);
    setSearchTerm(employee);
    setShowDropdown(false);
  };

  const handleInputBlur = () => {
    setTimeout(() => {
      setShowDropdown(false);
    }, 300);
  };

  const handleDropdownMouseDown = (e) => {
    e.preventDefault();
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && selectedEmployee && question.trim()) {
      handleSubmit();
    }
  };

  return (
    <div className="form-container">
      {/* File Upload Section */}
      <div className="upload-section">
        <div className="section-header">
          <div className="icon-wrapper upload-icon">
            <Upload className="icon" />
          </div>
          <h3 className="section-title">Upload Files</h3>
        </div>

        <div className="upload-form">
          <div className="file-inputs-grid">
            <div className="file-input-group">
              <label className="file-label">
                <FileText className="label-icon" />
                Employee Data (CSV/XLSX)
              </label>
              <div className="file-input-wrapper">
                <input
                  id="emp-file-input"
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={(e) => setEmpFile(e.target.files[0])}
                  className="file-input"
                />
                {empFile && (
                  <div className="file-name-display">
                    <CheckCircle className="file-check-icon" />
                    Selected: {empFile.name}
                  </div>
                )}
                {!empFile && lastUploadedEmpFile && (
                  <div className="file-name-display">
                    <CheckCircle className="file-check-icon" />
                    ✅ Uploaded: {lastUploadedEmpFile}
                  </div>
                )}
              </div>
            </div>

            <div className="file-input-group">
              <label className="file-label">
                <FileText className="label-icon" />
                Policy Document (PDF)
              </label>
              <div className="file-input-wrapper">
                <input
                  id="policy-file-input"
                  type="file"
                  accept="application/pdf"
                  onChange={(e) => setPolicyFile(e.target.files[0])}
                  className="file-input"
                />
                {policyFile && (
                  <div className="file-name-display">
                    <CheckCircle className="file-check-icon" />
                    Selected: {policyFile.name}
                  </div>
                )}
                {!policyFile && lastUploadedPolicyFile && (
                  <div className="file-name-display">
                    <CheckCircle className="file-check-icon" />
                    ✅ Uploaded: {lastUploadedPolicyFile}
                  </div>
                )}
              </div>
            </div>
          </div>

          <button
            onClick={handleUpload}
            disabled={isUploading || !empFile || !policyFile}
            className="upload-button"
          >
            {isUploading ? (
              <>
                <div className="spinner"></div>
                Uploading...
              </>
            ) : (
              <>
                <Upload className="button-icon" />
                Upload Files
              </>
            )}
          </button>
        </div>
      </div>

      {/* Question Section */}
      <div className="question-section">
        <div className="section-header">
          <div className="icon-wrapper question-icon">
            <MessageSquare className="icon" />
          </div>
          <h3 className="section-title">Ask Assistant</h3>
        </div>

        <div className="question-form">
          <div className="employee-select-group">
            <label className="question-label">
              <Users className="label-icon" />
              Select Employee
            </label>
            <div className="search-container">
              <div className="search-input-wrapper">
                <Search className="search-icon" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => {
                    setSearchTerm(e.target.value);
                    setShowDropdown(true);
                  }}
                  onFocus={() => setShowDropdown(true)}
                  onBlur={handleInputBlur}
                  placeholder="Type to search employees..."
                  className="search-input"
                />
              </div>

              {showDropdown && filteredEmployees.length > 0 && (
                <div className="dropdown" onMouseDown={handleDropdownMouseDown}>
                  {filteredEmployees.slice(0, 10).map((employee, index) => (
                    <button
                      key={index}
                      type="button"
                      onClick={() => handleEmployeeSelect(employee)}
                      className="dropdown-item"
                    >
                      {employee}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="question-input-group">
            <label className="question-label">
              Enter Your Question
            </label>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about leave, raise, task load, performance, policies..."
              required
              rows={4}
              className="question-textarea"
            />
            {question.trim() && (
              <button
                onClick={clearQuestion}
                type="button"
                className="clear-question-btn"
              >
                Clear Question
              </button>
            )}
          </div>

          <button
            onClick={handleSubmit}
            disabled={!selectedEmployee || !question.trim()}
            className="ask-button"
          >
            <MessageSquare className="button-icon" />
            Ask Assistant
          </button>
        </div>
      </div>

      <style jsx>{`
        .file-name-display {
          margin-top: 8px;
          padding: 8px 12px;
          background-color: #f0f9ff;
          border: 1px solid #bfdbfe;
          border-radius: 6px;
          font-size: 14px;
          color: #1e40af;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .file-check-icon {
          width: 16px;
          height: 16px;
          color: #059669;
        }

        .clear-question-btn {
          margin-top: 8px;
          padding: 4px 12px;
          background-color: #f3f4f6;
          border: 1px solid #d1d5db;
          border-radius: 4px;
          font-size: 12px;
          color: #6b7280;
          cursor: pointer;
          transition: background-color 0.2s;
        }

        .clear-question-btn:hover {
          background-color: #e5e7eb;
          color: #374151;
        }
      `}</style>
    </div>
  );
};

export default QuestionForm;
