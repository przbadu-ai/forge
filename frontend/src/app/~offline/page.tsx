"use client";

export default function OfflinePage() {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        backgroundColor: "#0a0a0a",
        color: "#fafafa",
        fontFamily: "system-ui, sans-serif",
        padding: "2rem",
        textAlign: "center",
      }}
    >
      <svg
        width="64"
        height="64"
        viewBox="0 0 64 64"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{ marginBottom: "1.5rem" }}
      >
        <rect width="64" height="64" rx="10" fill="#1a1a1a" />
        <text
          x="50%"
          y="54%"
          dominantBaseline="middle"
          textAnchor="middle"
          fontFamily="system-ui, sans-serif"
          fontWeight="bold"
          fontSize="38"
          fill="#fafafa"
        >
          F
        </text>
      </svg>
      <h1
        style={{
          fontSize: "1.5rem",
          fontWeight: 600,
          marginBottom: "0.75rem",
          marginTop: 0,
        }}
      >
        You are offline
      </h1>
      <p
        style={{
          color: "#a1a1a1",
          marginBottom: "2rem",
          maxWidth: "24rem",
          lineHeight: 1.5,
        }}
      >
        Forge needs a connection to your backend to work. Check your network
        and try again.
      </p>
      <button
        onClick={() => window.location.reload()}
        style={{
          padding: "0.75rem 1.5rem",
          backgroundColor: "#fafafa",
          color: "#0a0a0a",
          border: "none",
          borderRadius: "0.5rem",
          cursor: "pointer",
          fontSize: "1rem",
          fontWeight: 500,
        }}
      >
        Retry
      </button>
      <script
        dangerouslySetInnerHTML={{
          __html: `window.addEventListener("online", function() { window.location.reload(); });`,
        }}
      />
    </div>
  );
}
