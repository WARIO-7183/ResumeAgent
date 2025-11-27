import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = 'http://localhost:5000/api';

function App() {
  const [activeTab, setActiveTab] = useState('upload');
  const [resumes, setResumes] = useState([]);
  const [folders, setFolders] = useState([]);
  const [selectedFolder, setSelectedFolder] = useState('');
  const [selectedResumes, setSelectedResumes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [results, setResults] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  
  // Scan configuration
  const [jobDescription, setJobDescription] = useState('Looking for a skilled software engineer with experience in backend development.');
  const [skills, setSkills] = useState('python, machine learning, communication');

  useEffect(() => {
    if (activeTab === 'gmail') {
      fetchFolders();
    }
  }, [activeTab]);

  useEffect(() => {
    if (selectedFolder !== null) {
      fetchResumes(selectedFolder);
    }
  }, [selectedFolder]);

  const fetchFolders = async () => {
    try {
      const response = await axios.get(`${API_URL}/folders`);
      if (response.data.success) {
        setFolders(response.data.folders);
        if (response.data.folders.length > 0) {
          setSelectedFolder(response.data.folders[0]);
        }
      }
    } catch (error) {
      console.error('Error fetching folders:', error);
    }
  };

  const fetchResumes = async (folder) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/resumes`, {
        params: { folder }
      });
      if (response.data.success) {
        setResumes(response.data.resumes);
      }
    } catch (error) {
      console.error('Error fetching resumes:', error);
    }
    setLoading(false);
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setScanning(true);
    setUploadResult(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('job_description', jobDescription);
    formData.append('skills', skills);

    try {
      const response = await axios.post(`${API_URL}/scan-upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setUploadResult(response.data);
    } catch (error) {
      setUploadResult({ success: false, error: error.message });
    }
    setScanning(false);
  };

  const toggleResumeSelection = (storagePath) => {
    setSelectedResumes(prev => 
      prev.includes(storagePath)
        ? prev.filter(p => p !== storagePath)
        : [...prev, storagePath]
    );
  };

  const selectAllResumes = () => {
    if (selectedResumes.length === resumes.length) {
      setSelectedResumes([]);
    } else {
      setSelectedResumes(resumes.map(r => r.storage_path));
    }
  };

  const scanSelectedResumes = async () => {
    if (selectedResumes.length === 0) return;

    setScanning(true);
    setResults(null);

    try {
      const response = await axios.post(`${API_URL}/scan`, {
        storage_paths: selectedResumes,
        job_description: jobDescription,
        skills: skills.split(',').map(s => s.trim())
      });
      setResults(response.data);
    } catch (error) {
      setResults({ success: false, error: error.message });
    }
    setScanning(false);
  };

  const getScoreColor = (score) => {
    if (score >= 8) return '#10b981';
    if (score >= 6) return '#f59e0b';
    if (score >= 4) return '#f97316';
    return '#ef4444';
  };

  const getScoreGrade = (score) => {
    if (score >= 9) return 'A+';
    if (score >= 8) return 'A';
    if (score >= 7) return 'B+';
    if (score >= 6) return 'B';
    if (score >= 5) return 'C';
    return 'D';
  };

  return (
    <div className="app">
      <header className="header">
        <div className="logo">
          <span className="logo-icon">◈</span>
          <h1>Resume Scanner</h1>
        </div>
        <p className="tagline">AI-Powered Resume Evaluation</p>
      </header>

      <nav className="tabs">
        <button 
          className={`tab ${activeTab === 'upload' ? 'active' : ''}`}
          onClick={() => setActiveTab('upload')}
        >
          <span className="tab-icon">↑</span>
          Direct Upload
        </button>
        <button 
          className={`tab ${activeTab === 'gmail' ? 'active' : ''}`}
          onClick={() => setActiveTab('gmail')}
        >
          <span className="tab-icon">✉</span>
          Gmail Resumes
        </button>
      </nav>

      <main className="main">
        {/* Configuration Panel */}
        <section className="config-panel">
          <h3>Evaluation Settings</h3>
          <div className="config-grid">
            <div className="config-field">
              <label>Job Description</label>
              <textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="Enter job description..."
                rows={3}
              />
            </div>
            <div className="config-field">
              <label>Skills to Evaluate (comma-separated)</label>
              <input
                type="text"
                value={skills}
                onChange={(e) => setSkills(e.target.value)}
                placeholder="python, machine learning, communication"
              />
            </div>
          </div>
        </section>

        {activeTab === 'upload' && (
          <section className="upload-section">
            <div className="upload-area">
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileUpload}
                id="file-upload"
                disabled={scanning}
              />
              <label htmlFor="file-upload" className="upload-label">
                {scanning ? (
                  <>
                    <div className="spinner"></div>
                    <span>Analyzing Resume...</span>
                  </>
                ) : (
                  <>
                    <span className="upload-icon">📄</span>
                    <span>Drop PDF here or click to upload</span>
                    <span className="upload-hint">Supports PDF files only</span>
                  </>
                )}
              </label>
            </div>

            {uploadResult && (
              <div className="result-card single-result">
                {uploadResult.success ? (
                  <>
                    <div className="result-header">
                      <h3>{uploadResult.filename}</h3>
                      <div 
                        className="score-badge"
                        style={{ backgroundColor: getScoreColor(uploadResult.final_score) }}
                      >
                        <span className="score-grade">{getScoreGrade(uploadResult.final_score)}</span>
                        <span className="score-value">{uploadResult.final_score}/10</span>
                      </div>
                    </div>
                    <div className="breakdown">
                      <h4>Score Breakdown</h4>
                      <div className="breakdown-grid">
                        {Object.entries(uploadResult.breakdown || {}).map(([key, value]) => (
                          <div key={key} className="breakdown-item">
                            <span className="breakdown-label">{key.replace(/_/g, ' ')}</span>
                            <div className="breakdown-bar">
                              <div 
                                className="breakdown-fill"
                                style={{ 
                                  width: `${value * 10}%`,
                                  backgroundColor: getScoreColor(value)
                                }}
                              />
                            </div>
                            <span className="breakdown-value">{value}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="details">
                      <h4>Detailed Analysis</h4>
                      {Object.entries(uploadResult.details || {}).map(([key, detail]) => (
                        <div key={key} className="detail-item">
                          <strong>{key.replace(/_/g, ' ')}:</strong>
                          <p>{detail.explanation}</p>
                        </div>
                      ))}
                    </div>
                  </>
                ) : (
                  <div className="error">Error: {uploadResult.error}</div>
                )}
              </div>
            )}
          </section>
        )}

        {activeTab === 'gmail' && (
          <section className="gmail-section">
            <div className="gmail-controls">
              <div className="folder-select">
                <label>Select Date Folder:</label>
                <select 
                  value={selectedFolder} 
                  onChange={(e) => setSelectedFolder(e.target.value)}
                >
                  <option value="">Root</option>
                  {folders.map(folder => (
                    <option key={folder} value={folder}>{folder}</option>
                  ))}
                </select>
              </div>
              <div className="action-buttons">
                <button 
                  className="btn btn-secondary"
                  onClick={selectAllResumes}
                >
                  {selectedResumes.length === resumes.length ? 'Deselect All' : 'Select All'}
                </button>
                <button 
                  className="btn btn-primary"
                  onClick={scanSelectedResumes}
                  disabled={selectedResumes.length === 0 || scanning}
                >
                  {scanning ? 'Scanning...' : `Scan Selected (${selectedResumes.length})`}
                </button>
              </div>
            </div>

            {loading ? (
              <div className="loading">
                <div className="spinner"></div>
                <p>Loading resumes...</p>
              </div>
            ) : (
              <div className="resume-list">
                {resumes.length === 0 ? (
                  <div className="empty-state">
                    <span className="empty-icon">📭</span>
                    <p>No resumes found in this folder</p>
                  </div>
                ) : (
                  resumes.map(resume => (
                    <div 
                      key={resume.storage_path}
                      className={`resume-item ${selectedResumes.includes(resume.storage_path) ? 'selected' : ''}`}
                      onClick={() => toggleResumeSelection(resume.storage_path)}
                    >
                      <div className="checkbox">
                        {selectedResumes.includes(resume.storage_path) && '✓'}
                      </div>
                      <div className="resume-info">
                        <span className="resume-name">{resume.name}</span>
                        <span className="resume-path">{resume.storage_path}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {results && (
              <div className="results-section">
                <h3>Scan Results</h3>
                {results.success ? (
                  <div className="results-grid">
                    {results.results.map((result, index) => (
                      <div key={index} className="result-card">
                        {result.success ? (
                          <>
                            <div className="result-header">
                              <h4>{result.filename}</h4>
                              <div 
                                className="score-badge"
                                style={{ backgroundColor: getScoreColor(result.final_score) }}
                              >
                                <span className="score-grade">{getScoreGrade(result.final_score)}</span>
                                <span className="score-value">{result.final_score}/10</span>
                              </div>
                            </div>
                            <div className="breakdown">
                              <div className="breakdown-grid">
                                {Object.entries(result.breakdown || {}).map(([key, value]) => (
                                  <div key={key} className="breakdown-item">
                                    <span className="breakdown-label">{key.replace(/_/g, ' ')}</span>
                                    <div className="breakdown-bar">
                                      <div 
                                        className="breakdown-fill"
                                        style={{ 
                                          width: `${value * 10}%`,
                                          backgroundColor: getScoreColor(value)
                                        }}
                                      />
                                    </div>
                                    <span className="breakdown-value">{value}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                            <details className="details-accordion">
                              <summary>View Details</summary>
                              <div className="details">
                                {Object.entries(result.details || {}).map(([key, detail]) => (
                                  <div key={key} className="detail-item">
                                    <strong>{key.replace(/_/g, ' ')}:</strong>
                                    <p>{detail.explanation}</p>
                                  </div>
                                ))}
                              </div>
                            </details>
                          </>
                        ) : (
                          <div className="error">
                            <h4>{result.filename}</h4>
                            <p>Error: {result.error}</p>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="error">Error: {results.error}</div>
                )}
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
}

export default App;

