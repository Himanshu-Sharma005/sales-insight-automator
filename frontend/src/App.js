import React, { useState, useRef, useCallback } from "react";
import "./App.css";

const API_BASE = process.env.REACT_APP_API_URL || "";

function App() {
  const [file, setFile] = useState(null);
  const [email, setEmail] = useState("");
  const [dragging, setDragging] = useState(false);
  const [status, setStatus] = useState("idle"); // idle | loading | success | error
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const fileInputRef = useRef();

  const handleFile = useCallback((f) => {
    if (!f) return;
    const ext = f.name.split(".").pop().toLowerCase();
    if (!["csv", "xlsx", "xls"].includes(ext)) {
      setErrorMsg("Only .csv and .xlsx files are supported.");
      return;
    }
    if (f.size > 10 * 1024 * 1024) {
      setErrorMsg("File exceeds 10MB limit.");
      return;
    }
    setErrorMsg("");
    setFile(f);
    setResult(null);
    setStatus("idle");
  }, []);

  const onDrop = useCallback(
    (e) => {
      e.preventDefault();
      setDragging(false);
      const f = e.dataTransfer.files[0];
      handleFile(f);
    },
    [handleFile],
  );

  const onDragOver = (e) => {
    e.preventDefault();
    setDragging(true);
  };
  const onDragLeave = () => setDragging(false);

  const handleSubmit = async () => {
    if (!file || !email) return;
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setErrorMsg("Please enter a valid email address.");
      return;
    }

    setStatus("loading");
    setErrorMsg("");
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("recipient_email", email);

    try {
      const res = await fetch(`${API_BASE}/api/v1/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || `Server error: ${res.status}`);
      }

      setResult(data);
      setStatus("success");
    } catch (err) {
      setErrorMsg(err.message || "Something went wrong. Please try again.");
      setStatus("error");
    }
  };

  const reset = () => {
    setFile(null);
    setEmail("");
    setStatus("idle");
    setResult(null);
    setErrorMsg("");
  };

  const formatRevenue = (num) => {
    if (!num) return "—";
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(num);
  };

  return (
    <div className="app">
      {/* Background */}
      <div className="bg-grid" />
      <div className="bg-glow" />

      {/* Header */}
      <header className="header">
        <div className="header-inner">
          <div className="logo">
            <span className="logo-icon">◈</span>
            <span className="logo-text">
              Rabbitt<em>AI</em>
            </span>
          </div>
          <nav className="nav">
            <a
              href={`${API_BASE}/docs`}
              target="_blank"
              rel="noreferrer"
              className="nav-link"
            >
              API Docs <span className="nav-arrow">↗</span>
            </a>
          </nav>
        </div>
      </header>

      <main className="main">
        {/* Hero */}
        <section className="hero">
          <div className="hero-tag">Sales Intelligence Tool</div>
          <h1 className="hero-title">
            Turn Raw Data Into
            <br />
            <em>Executive Clarity</em>
          </h1>
          <p className="hero-sub">
            Upload your Q-report. Our AI distills it into a board-ready briefing
            — delivered to any inbox in seconds.
          </p>
        </section>

        {/* Card */}
        <div className="card">
          {status === "success" ? (
            <SuccessView
              result={result}
              onReset={reset}
              formatRevenue={formatRevenue}
            />
          ) : (
            <UploadView
              file={file}
              email={email}
              setEmail={setEmail}
              dragging={dragging}
              status={status}
              errorMsg={errorMsg}
              fileInputRef={fileInputRef}
              handleFile={handleFile}
              onDrop={onDrop}
              onDragOver={onDragOver}
              onDragLeave={onDragLeave}
              handleSubmit={handleSubmit}
            />
          )}
        </div>

        {/* Trust strip */}
        <div className="trust-strip">
          <span>🔒 Encrypted in transit</span>
          <span>⚡ OpenAI powered analysis</span>
          <span>📧 Delivered to inbox</span>
          <span>🛡️ Rate-limited API</span>
        </div>
      </main>

      <footer className="footer">
        <p>Sales Insight Automator · Built for Rabbitt AI Sprint · 2026</p>
      </footer>
    </div>
  );
}

function UploadView({
  file,
  email,
  setEmail,
  dragging,
  status,
  errorMsg,
  fileInputRef,
  handleFile,
  onDrop,
  onDragOver,
  onDragLeave,
  handleSubmit,
}) {
  const isLoading = status === "loading";
  const canSubmit = file && email && !isLoading;

  return (
    <div className="upload-view">
      <div className="card-header">
        <h2>Analyze Sales Data</h2>
        <p>
          Upload a CSV or Excel file · Receive an AI-generated executive summary
        </p>
      </div>

      {/* Drop Zone */}
      <div
        className={`dropzone ${dragging ? "dragging" : ""} ${file ? "has-file" : ""}`}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          style={{ display: "none" }}
          onChange={(e) => handleFile(e.target.files[0])}
        />
        {file ? (
          <div className="file-info">
            <span className="file-icon">
              {file.name.endsWith(".csv") ? "🗂️" : "📊"}
            </span>
            <div>
              <div className="file-name">{file.name}</div>
              <div className="file-size">
                {(file.size / 1024).toFixed(1)} KB · Ready to analyze
              </div>
            </div>
            <button
              className="clear-btn"
              onClick={(e) => {
                e.stopPropagation();
                handleFile(null);
              }}
              title="Remove file"
            >
              ✕
            </button>
          </div>
        ) : (
          <div className="drop-prompt">
            <div className="drop-icon">⤓</div>
            <div className="drop-text">
              Drop your file here, or <span className="link-text">browse</span>
            </div>
            <div className="drop-hint">CSV or XLSX · Max 10MB</div>
          </div>
        )}
      </div>

      {/* Email Input */}
      <div className="input-group">
        <label className="input-label">Recipient Email</label>
        <div className="input-wrapper">
          <span className="input-icon">@</span>
          <input
            type="email"
            className="email-input"
            placeholder="executive@company.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={isLoading}
          />
        </div>
      </div>

      {/* Error */}
      {errorMsg && (
        <div className="error-banner">
          <span>⚠</span> {errorMsg}
        </div>
      )}

      {/* Submit */}
      <button
        className={`submit-btn ${isLoading ? "loading" : ""}`}
        onClick={handleSubmit}
        disabled={!canSubmit}
      >
        {isLoading ? (
          <>
            <span className="spinner" /> Analyzing with AI...
          </>
        ) : (
          <>Generate & Send Report ↗</>
        )}
      </button>

      {isLoading && (
        <div className="loading-steps">
          <div className="step active">Parsing data file</div>
          <div className="step">Generating AI summary</div>
          <div className="step">Sending to inbox</div>
        </div>
      )}
    </div>
  );
}

function SuccessView({ result, onReset, formatRevenue }) {
  return (
    <div className="success-view">
      <div className="success-icon">✓</div>
      <h2>Report Delivered!</h2>
      <p className="success-sub">
        Your executive summary has been sent to{" "}
        <strong>{result.recipient}</strong>
      </p>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">File Analyzed</div>
          <div className="stat-value file-stat">{result.filename}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Rows Processed</div>
          <div className="stat-value">{result.rows_analyzed}</div>
        </div>
      </div>

      <div className="preview-box">
        <div className="preview-label">Summary Preview</div>
        <p className="preview-text">{result.summary_preview}</p>
      </div>

      <button className="submit-btn reset-btn" onClick={onReset}>
        ← Analyze Another File
      </button>
    </div>
  );
}

export default App;
