import { useState } from "react";
import { login } from "shared/api";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [pass, setPass] = useState("");
  const [result, setResult] = useState(null);

  const handleLogin = async () => {
    try {
        const res = await login(email, pass);
        
        console.log("LOGIN RESPONSE:", setResult(res.data));
        
        // 🔥 Validación REAL del backend
        if (!res.data.success) {
            alert("Error", "Credenciales incorrectas");
            return;
        }
        
        alert("Éxito", "Inicio de sesión correcto");
        navigation.navigate("/home"); // ahora sí
      /*const res = await login(email, pass);
      setResult(res.data);
      navigate("/home");*/
    } catch (error) {
      console.log("ERROR LOGIN WEB:", error);
      console.log("DATA:", error?.response?.data);

      alert(
        "Error al iniciar sesión ❌\n\n" +
        JSON.stringify(error?.response?.data ?? "Sin respuesta del servidor", null, 2)
      );
    }
  };

  return (
    <div style={{ padding: 40 }}>
      <h1>Login</h1>

      <input value={email} placeholder="Correo" onChange={e => setEmail(e.target.value)} />
      <br />

      <input type="password" value={pass} placeholder="Clave" onChange={e => setPass(e.target.value)} />
      <br />

      <button onClick={handleLogin}>Entrar</button>

      <button onClick={() => navigate("/register")}>Crear cuenta</button>

      <pre>{JSON.stringify(result, null, 2)}</pre>
    </div>
  );
}
