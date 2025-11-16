// src/components/Navbar.jsx
export default function Navbar({ onMenuPress }) {
  return (
    <div style={{
      padding: "15px",
      display: "flex",
      justifyContent: "flex-end"
    }}>
      <button
        style={{
          fontSize: 28,
          background: "none",
          border: "none",
          cursor: "pointer"
        }}
        onClick={onMenuPress}
      >
        ☰
      </button>
    </div>
  );
}
