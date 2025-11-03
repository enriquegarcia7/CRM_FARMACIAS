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
import Sales from './pages/Sales/Sales';
import ETL from './pages/ETL/ETL';

function App() {
  return (
    <BrowserRouter>
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
            <Route path="ventas" element={<Sales />} />
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
