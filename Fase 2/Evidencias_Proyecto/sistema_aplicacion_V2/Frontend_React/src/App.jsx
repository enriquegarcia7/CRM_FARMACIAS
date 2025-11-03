import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/layout/Layout';
import Login from './pages/Login/Login';
import Dashboard from './pages/Dashboard/Dashboard';
import Inventory from './pages/Inventory/Inventory';
import Customers from './pages/Customers/Customers';
import PurchaseSuggestions from './pages/PurchaseSuggestions/PurchaseSuggestions';
import OfertasLaboratorio from './pages/OfertasLaboratorio/OfertasLaboratorio';
import ETL from './pages/ETL/ETL';
import SeasonalDemand from './pages/SeasonalDemand/SeasonalDemand';  // ← NUEVO

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="inventario" element={<Inventory />} />
          <Route path="clientes" element={<Customers />} />
          <Route path="sugerencias" element={<PurchaseSuggestions />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
