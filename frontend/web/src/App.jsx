import { useState } from "react";
import { login } from "shared/api";

function App() {
  const [email, setEmail] = useState("");
  const [pass, setPass] = useState("");
  const [result, setResult] = useState(null);

  const handleLogin = async () => {
    try {
      // Aquí corregimos la llamada
      const res = await login(email, pass);

      console.log("LOGIN WEB OK:", res.data);

      alert(
        "Inicio de sesión correcto ✅\n\n" +
        JSON.stringify(res.data, null, 2)
      );

      setResult(res.data);

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

      <input
        type="text"
        placeholder="Correo"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />

      <input
        type="password"
        placeholder="Clave"
        value={pass}
        onChange={(e) => setPass(e.target.value)}
      />

      <button onClick={handleLogin}>Entrar</button>

      <pre>{JSON.stringify(result, null, 2)}</pre>
    </div>
  );
}

export default App;
