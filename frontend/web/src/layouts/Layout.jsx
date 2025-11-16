// layout/Layout.jsx
import { useState } from "react";
import Sidebar from "../components/Sidebar";
import  "../styles/layout.css";

export default function Layout({ children }) {
  const [open, setOpen] = useState(false);

  return (
    <div style={{ display: "flex" }}>
      
      {/* Sidebar */}
      <Sidebar open={open} onClose={() => setOpen(false)} />

      {/* Contenido principal */}
      <main style={{ flex: 1, padding: 20, position: "relative" }}>
        
        {/* Botón del menú */}
        <button
          style={{
            position: "absolute",
            right: 20,
            top: 20,
            background: "#4f46e5",
            color: "white",
            padding: "10px 14px",
            borderRadius: 8,
            cursor: "pointer",
            border: "none",
            fontSize: 18
          }}
          onClick={() => setOpen(true)}
        >
          ☰
        </button>

        {/* Aquí se renderiza Home.jsx */}
        {children}

      </main>
    </div>
  );
}


