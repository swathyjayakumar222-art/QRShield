import { useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export default function App() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [results, setResults] = useState([]);

  async function handleScan(event) {
    event.preventDefault();
    if (!file) return setError("Choose a QR image first.");
    setLoading(true);
    setError("");
    setResults([]);
    const form = new FormData();
    form.append("file", file);
    try {
      const response = await fetch(API_BASE + "/api/scan", { method: "POST", body: form });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Scan failed.");
      setResults(data.results || []);
    } catch (err) {
      setError(err.message || "Could not connect to the API.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="shell">
      <nav className="nav"><a className="brand" href="/"><span className="mark">Q</span> QRShield</a><span>QR destination awareness</span></nav>
      <section className="hero">
        <div className="eyebrow"><i /> A SAFER WAY TO SCAN</div>
        <h1>Look beyond the<br /><span>QR code.</span></h1>
        <p className="intro">Inspect what a QR code contains and understand potential warning signs before visiting its destination.</p>
        <form className="upload" onSubmit={handleScan}>
          <div className="scan-icon">▦</div>
          <h2>Scan a QR code</h2>
          <p>Upload an image containing a QR code. We decode it without opening its destination.</p>
          <label className="file">
            <input type="file" accept="image/png,image/jpeg,image/webp" onChange={e => { setFile(e.target.files?.[0] || null); setError(""); setResults([]); }} />
            {file ? file.name : "Choose QR image"}
          </label>
          <button disabled={!file || loading}>{loading ? "Analysing…" : "Analyse QR code"} <span>↗</span></button>
          {error && <p className="error" role="alert">{error}</p>}
          <small>▣ &nbsp;Image is processed for this request only.</small>
        </form>
      </section>

      {results.length > 0 && <section className="results">
        <h2>Scan results</h2>
        {results.map((item, index) => <article className="result" key={index}>
          <div className="result-head">
            <span className="type">{item.payload_type.replaceAll("_", " ")}</span>
            {item.risk_assessment && <span className={"risk " + item.risk_assessment.risk_level}>{item.risk_assessment.risk_level} risk · {item.risk_assessment.risk_score}/100</span>}
          </div>
          <p className="payload">{item.payload}</p>
          {item.risk_assessment ? <>
            <h3>What we noticed</h3>
            <ul>{item.risk_assessment.findings.map(f => <li key={f.code}><b>{f.severity}:</b> {f.message}</li>)}</ul>
            <p className="disclaimer">{item.risk_assessment.disclaimer}</p>
          </> : <p className="disclaimer">Displayed as decoded content only. QRShield has not opened or executed it.</p>}
        </article>)}
      </section>}

      <footer><b>QRShield</b><span>Research prototype · A low score is not a safety guarantee.</span></footer>
    </main>
  );
}
