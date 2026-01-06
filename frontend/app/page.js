// src/app/page.js
"use client";

import { useState } from "react";

const API = typeof window !== "undefined" && window.location.hostname === "localhost"
  ? "http://127.0.0.1:8000"
  : "http://127.0.0.1:8000"; // change if your backend sits elsewhere

export default function Home() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const [topK, setTopK] = useState(4);

  const [question, setQuestion] = useState("");
  const [queryAnswer, setQueryAnswer] = useState(null);

  const [certificateData, setCertificateData] = useState(null);
  const [filledForm, setFilledForm] = useState(null);
  const [formFields, setFormFields] = useState("person_name,date_of_birth,category_or_caste");

  const [rawResponse, setRawResponse] = useState(null);
  const [error, setError] = useState(null);

  function resetResponseState() {
    setError(null);
    setRawResponse(null);
  }

  async function uploadFile() {
    if (!file) return alert("Choose a file first");
    resetResponseState();
    setLoading(true);
    setStatus("Uploading document...");
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${API}/upload`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) {
        const t = await res.text();
        throw new Error(`Upload failed: ${res.status} ${t}`);
      }
      const data = await res.json();
      setStatus(`Uploaded. Indexed ${data.num_chunks} chunks.`);
    } catch (e) {
      console.error(e);
      setError(e.message || String(e));
      setStatus("Upload failed");
    } finally {
      setLoading(false);
    }
  }

  async function analyzeCertificate() {
    resetResponseState();
    setLoading(true);
    setStatus("Analyzing certificate...");
    try {
      const res = await fetch(`${API}/analyze/certificate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: "extract certificate fields", top_k: topK }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || JSON.stringify(data));
      setCertificateData(data.parsed ?? null);
      setRawResponse(data.raw ?? data);
      setStatus("Certificate analysis complete");
    } catch (e) {
      console.error(e);
      setError(e.message || String(e));
      setStatus("Certificate analysis failed");
    } finally {
      setLoading(false);
    }
  }

  async function askQuestion() {
    if (!question.trim()) return alert("Enter a question");
    resetResponseState();
    setLoading(true);
    setStatus("Querying document...");
    try {
      const res = await fetch(`${API}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, top_k: topK }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || JSON.stringify(data));
      setQueryAnswer(data);
      setRawResponse(data);
      setStatus("Query finished");
    } catch (e) {
      console.error(e);
      setError(e.message || String(e));
      setStatus("Query failed");
    } finally {
      setLoading(false);
    }
  }

  async function fillForm() {
    resetResponseState();
    if (!formFields.trim()) return alert("Enter fields to extract, comma separated.");
    setLoading(true);
    setStatus("Filling fields...");
    try {
      const fields = formFields.split(",").map((s) => s.trim()).filter(Boolean);
      const res = await fetch(`${API}/fill-form`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fields, top_k: topK }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || JSON.stringify(data));
      setFilledForm(data.result ?? null);
      setRawResponse(data);
      setStatus("Form filled");
    } catch (e) {
      console.error(e);
      setError(e.message || String(e));
      setStatus("Fill form failed");
    } finally {
      setLoading(false);
    }
  }

  function downloadRaw() {
    if (!rawResponse) return;
    const blob = new Blob([JSON.stringify(rawResponse, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "rag_response.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div style={{ maxWidth: 900, margin: "28px auto", fontFamily: "Inter, Arial, sans-serif" }}>
      <h1 style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <span style={{ fontSize: 26 }}>📄</span>
        <div>
          <div style={{ fontSize: 28, fontWeight: 700 }}>RAG Certificate Analyzer</div>
          <div style={{ color: "#666", fontSize: 13 }}>Certificate analyzer · Document QA · Form filling</div>
        </div>
      </h1>

      <div style={{
        marginTop: 18,
        padding: 16,
        border: "1px solid rgba(255,255,255,0.06)",
        borderRadius: 10,
        background: "#0b1220",
        color: "#ddd"
      }}>
        <strong style={{ color: "#fff" }}>Options</strong>
        <div style={{ marginTop: 8, display: "flex", gap: 8, alignItems: "center" }}>
          <label style={{ fontSize: 13, color: "#cfd8e3" }}>Top K</label>
          <input
            type="number"
            min={1}
            max={12}
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
            style={{ width: 72, padding: 6, background: "#0f1724", color: "#fff", border: "1px solid rgba(255,255,255,0.06)", borderRadius: 6 }}
          />
          <div style={{ marginLeft: "auto", fontSize: 13, color: "#9aa" }}>{loading ? "Working..." : status}</div>
        </div>
      </div>

      <section style={{ marginTop: 18 }}>
        <h2 style={{ marginBottom: 8 }}>1. Upload Document</h2>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <input type="file" accept=".pdf,.txt" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          <button onClick={uploadFile} style={{ padding: "8px 12px" }}>Upload</button>
          <div style={{ color: "#666" }}>{file ? file.name : "No file selected"}</div>
        </div>
      </section>

      <section style={{ marginTop: 18 }}>
        <h2 style={{ marginBottom: 8 }}>2. Certificate Analysis (specialized)</h2>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={analyzeCertificate} style={{ padding: "8px 12px" }}>Analyze Certificate</button>
          <div style={{ color: "#666", alignSelf: "center" }}>Extract name, DOB, caste, issuing authority, etc.</div>
        </div>

        {certificateData && (
          <div style={{ marginTop: 12, background: "#fff", border: "1px solid #eee", padding: 12, borderRadius: 6 }}>
            <h3 style={{ margin: "0 0 8px 0" }}>Extracted Certificate Fields</h3>
            <div style={{ display: "grid", gap: 6 }}>
              {Object.entries(certificateData).map(([k, v]) => (
                <div key={k}><strong>{k.replaceAll("_", " ")}:</strong> {v === null ? <em>Not found</em> : String(v)}</div>
              ))}
            </div>
          </div>
        )}
      </section>

      <section style={{ marginTop: 18 }}>
        <h2 style={{ marginBottom: 8 }}>3. Ask a Question (Document QA)</h2>
        <textarea value={question} onChange={(e) => setQuestion(e.target.value)} rows={4} placeholder="Ask anything about the uploaded document" style={{ width: "100%", padding: 10 }} />
        <div style={{ marginTop: 8, display: "flex", gap: 8 }}>
          <button onClick={askQuestion} style={{ padding: "8px 12px" }}>Ask</button>
          <div style={{ color: "#666", alignSelf: "center" }}>Answers come with page excerpts when available.</div>
        </div>

        {queryAnswer && (
          <div style={{ marginTop: 12, background: "#fff", border: "1px solid #eee", padding: 12, borderRadius: 6 }}>
            <h3 style={{ margin: "0 0 8px 0" }}>Answer</h3>
            <div style={{ whiteSpace: "pre-wrap" }}>{queryAnswer.answer ?? JSON.stringify(queryAnswer, null, 2)}</div>

            {Array.isArray(queryAnswer.sources) && queryAnswer.sources.length > 0 && (
              <>
                <h4 style={{ marginTop: 10 }}>Sources</h4>
                <ul>
                  {queryAnswer.sources.map((s, i) => (
                    <li key={i} style={{ marginBottom: 6 }}>
                      <strong>page:</strong> {s.page ?? "?"} — <span style={{ color: "#444" }}>{s.excerpt ?? ""}</span>
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>
        )}
      </section>

      <section style={{ marginTop: 18 }}>
        <h2 style={{ marginBottom: 8 }}>4. Fill Form Fields</h2>
        <div style={{ display: "flex", gap: 8 }}>
          <input value={formFields} onChange={(e) => setFormFields(e.target.value)} style={{ flex: 1, padding: 8 }} />
          <button onClick={fillForm} style={{ padding: "8px 12px" }}>Fill</button>
        </div>

        {filledForm && (
          <div style={{ marginTop: 12, background: "#fff", border: "1px solid #eee", padding: 12, borderRadius: 6 }}>
            <h3 style={{ margin: "0 0 8px 0" }}>Filled Fields</h3>
            <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(filledForm, null, 2)}</pre>
          </div>
        )}
      </section>

      <footer style={{ marginTop: 18 }}>
        {rawResponse && (
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <button onClick={downloadRaw} style={{ padding: "6px 10px" }}>Download Raw JSON</button>
            <div style={{ color: "#444" }}>Raw includes complete LLM output and context excerpts</div>
          </div>
        )}

        {error && (
          <div style={{ marginTop: 10, color: "#a00", background: "#fff3f3", padding: 8, borderRadius: 6 }}>
            <strong>Error:</strong> {error}
          </div>
        )}
      </footer>
    </div>
  );
}
