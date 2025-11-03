import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard/Dashboard';
import Inventory from './pages/Inventory/Inventory';
import Customers from './pages/Customers/Customers';
import PurchaseSuggestions from './pages/PurchaseSuggestions/PurchaseSuggestions';
import SeasonalDemand from './pages/SeasonalDemand/SeasonalDemand';  // ← NUEVO
import OfertasLaboratorio from './pages/OfertasLaboratorio/OfertasLaboratorio';
import ETL from './pages/ETL/ETL';

function App() {
  return (
    <BrowserRouter>

      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="inventario" element={<Inventory />} />
          <Route path="clientes" element={<Customers />} />
          <Route path="demanda-estacional" element={<SeasonalDemand />} />  {/* ← NUEVO */}
          <Route path="sugerencias" element={<PurchaseSuggestions />} />
        </Route>
      </Routes>

      <AuthProvider>
        <Routes>
          {/* Ruta pública de Login */}
          <Route path="/login" element={<Login />} />

          {/* Rutas protegidas */}
          <Route path="/" element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }>
            <Route index element={<Dashboard />} />
            <Route path="inventario" element={<Inventory />} />
            <Route path="clientes" element={<Customers />} />
            <Route path="sugerencias" element={<PurchaseSuggestions />} />
            <Route path="ofertas-laboratorio" element={<OfertasLaboratorio />} />
            <Route path="etl" element={<ETL />} />
          </Route>
        </Routes>
      </AuthProvider>

    </BrowserRouter>
  );
}

export default App;
