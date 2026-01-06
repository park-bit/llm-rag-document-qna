

import "./globals.css";

export const metadata = {
  title: "RAG Certificate Analyzer",
  description: "Upload certificates, extract fields, ask questions, fill forms",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <div style={styles.app}>
          <header style={styles.header}>
            <h1 style={styles.title}>📄 RAG Certificate Analyzer</h1>
            <p style={styles.subtitle}>
              Upload → Analyze → Ask → Fill forms
            </p>
          </header>

          <main style={styles.main}>{children}</main>

          <footer style={styles.footer}>
            <span>
              Backend: FastAPI · RAG · Groq · OCR
            </span>
          </footer>
        </div>
      </body>
    </html>
  );
}

const styles = {
  app: {
    minHeight: "100vh",
    display: "flex",
    flexDirection: "column",
  },
  header: {
    padding: "16px 20px",
    borderBottom: "1px solid var(--border)",
    background: "var(--panel-bg)",
  },
  title: {
    margin: 0,
    fontSize: "22px",
  },
  subtitle: {
    marginTop: "4px",
    fontSize: "14px",
    color: "var(--muted-2)",
  },
  main: {
    flex: 1,
    padding: "20px",
    maxWidth: "900px",
    width: "100%",
    margin: "0 auto",
  },
  footer: {
    padding: "10px 20px",
    borderTop: "1px solid var(--border)",
    background: "var(--panel-bg)",
    fontSize: "12px",
    color: "var(--muted)",
    textAlign: "center",
  },
};

