import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Layout from "./layouts/layout";
import Login from "./pages/Login";
import Register from "./pages/Register";

function App() {
  return (
    <BrowserRouter>
      <Routes>

        {/* LOGIN & REGISTER sin layout */}
        <Route path="/" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* HOME CON LAYOUT */}
        <Route
          path="/home"
          element={
            <Layout>
              <Home />
            </Layout>
          }
        />

      </Routes>
    </BrowserRouter>
  );
}

export default App;
