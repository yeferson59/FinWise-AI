// src/components/Sidebar.jsx
import "../styles/sidebar.css";
import { Link } from "react-router-dom";

export default function Sidebar({ open, onClose }) {
  return (
    <div className={`sidebar ${open ? "open" : ""}`}>
      <button className="close-btn" onClick={onClose}>×</button>

      <h3>Menú</h3>

      <Link to="/home">🏠 Inicio</Link>
      <Link to="/transactions">💸 Registrar transacción</Link>
      <Link to="/health">📊 Mi salud financiera</Link>
      <Link to="/assistant">🤖 Asistente virtual</Link>
      <Link to="/notifications">🔔 Notificaciones</Link>

      <button
        onClick={() => {
          localStorage.removeItem("token");
          window.location.href = "/";
        }}
      >
        🚪 Cerrar Sesión
      </button>
    </div>
  );
}
