import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading, user } = useAuth();

  console.log('🔒 ProtectedRoute - Estado:', { loading, isAuthenticated, user: user?.email });

  if (loading) {
    console.log('⏳ Verificando sesión...');
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        flexDirection: 'column',
        gap: '1rem'
      }}>
        <div style={{
          width: '50px',
          height: '50px',
          border: '4px solid #e5e7eb',
          borderTopColor: '#667eea',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }}></div>
        <p style={{ color: '#6b7280' }}>Verificando sesión...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    console.log('🚫 Acceso bloqueado - Redirigiendo a /login');
    return <Navigate to="/login" replace />;
  }

  console.log('✅ Acceso permitido - Usuario autenticado');
  return children;
}

export default ProtectedRoute;
