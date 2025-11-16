import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import Login from "./pages/Login";
import Register from "./pages/Register";
import Home from "./pages/Home";
import Layout from "./layouts/Layout";



ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        {/* Página de inicio por defecto → Login */}
        <Route path="/" element={<Login />} />

        {/* Registro */}
        <Route path="/register" element={<Register />} />

        {/* Home */}
        
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
  </React.StrictMode>
);





