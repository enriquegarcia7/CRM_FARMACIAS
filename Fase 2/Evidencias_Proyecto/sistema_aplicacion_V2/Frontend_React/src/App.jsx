import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard/Dashboard';
import Inventory from './pages/Inventory/Inventory';
import Customers from './pages/Customers/Customers';
import PurchaseSuggestions from './pages/PurchaseSuggestions/PurchaseSuggestions';

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
