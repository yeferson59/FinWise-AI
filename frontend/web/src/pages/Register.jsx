import { useState } from "react";
import { register } from "shared/api";
import { useNavigate } from "react-router-dom";

export default function Register() {
  const navigate = useNavigate();

  const [first, setFirst] = useState("");
  const [last, setLast] = useState("");
  const [email, setEmail] = useState("");
  const [pass, setPass] = useState("");

  const handleRegister = async () => {
    try {
      await register(first, last, email, pass);
      alert("Registro exitoso");
      navigate("/");
    } catch {
      alert("Error al registrarte");
    }
  };

  return (
    <div style={{ padding: 40 }}>
      <h1>Registro</h1>

      <input placeholder="Nombre" value={first} onChange={e => setFirst(e.target.value)} />
      <br />

      <input placeholder="Apellido" value={last} onChange={e => setLast(e.target.value)} />
      <br />

      <input placeholder="Correo" value={email} onChange={e => setEmail(e.target.value)} />
      <br />

      <input type="password" placeholder="Clave" value={pass} onChange={e => setPass(e.target.value)} />
      <br />

      <button onClick={handleRegister}>Crear cuenta</button>
    </div>
  );
}
