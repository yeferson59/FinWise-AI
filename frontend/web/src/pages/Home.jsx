import "../styles/home.css";

export default function Home() {
  return (
    <div className="home-container">

      {/* Título */}
      <div className="home-header">
        <h1>Cosmos Financiero</h1>
        <p>Tu universo de finanzas personales</p>
      </div>

      {/* Tarjetas principales */}
      <div className="cards-grid">

        <div className="card large">
          <p className="label">Balance Total</p>
          <h2 className="value">$12,450.50</h2>
          <span className="trend green">▲ +12.5%</span>
        </div>

        <div className="card">
          <p className="label">Ingresos</p>
          <h2 className="value">$5,200</h2>
        </div>

        <div className="card">
          <p className="label">Gastos</p>
          <h2 className="value">$3,890</h2>
        </div>

        <div className="card">
          <p className="label">Meta de Ahorro</p>
          <h2 className="value">$1,309</h2>
          <div className="progress-bar">
            <div className="progress" style={{ width: "65%" }}></div>
          </div>
          <span className="progress-text">65% completado</span>
        </div>

      </div>

    </div>
  );
}
