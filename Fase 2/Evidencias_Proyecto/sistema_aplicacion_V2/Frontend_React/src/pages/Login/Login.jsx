import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import './Login.css';

function Login() {
  const { login } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleGoogleLogin = async () => {
    try {
      console.log('🔑 Iniciando login con Google...');
      setLoading(true);
      setError('');

      const user = await login();
      console.log('✅ Login completado, usuario:', user);

      // Redirigir al dashboard después de login exitoso
      console.log('🔀 Redirigiendo a dashboard...');
      navigate('/', { replace: true });

    } catch (err) {
      console.error('❌ Error en login:', err);
      setError(err.message || 'Error al iniciar sesión con Google');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <div className="login-header">
          <div className="logo">
            <svg width="60" height="60" viewBox="0 0 60 60" fill="none">
              <rect width="60" height="60" rx="12" fill="#667eea"/>
              <path d="M30 15C21.716 15 15 21.716 15 30C15 38.284 21.716 45 30 45C38.284 45 45 38.284 45 30C45 21.716 38.284 15 30 15ZM30 18C36.627 18 42 23.373 42 30C42 36.627 36.627 42 30 42C23.373 42 18 36.627 18 30C18 23.373 23.373 18 30 18Z" fill="white"/>
              <path d="M30 22C25.582 22 22 25.582 22 30C22 34.418 25.582 38 30 38C34.418 38 38 34.418 38 30C38 25.582 34.418 22 30 22ZM30 25C32.761 25 35 27.239 35 30C35 32.761 32.761 35 30 35C27.239 35 25 32.761 25 30C25 27.239 27.239 25 30 25Z" fill="white"/>
            </svg>
          </div>
          <h1>SmartPharm CRM</h1>
          <p className="subtitle">Sistema de Gestión Farmacéutica</p>
        </div>

        <div className="login-content">
          <h2>Iniciar Sesión</h2>
          <p className="login-description">
            Ingresa con tu cuenta de Google para acceder al sistema.
            <br/>
            <small>Gmail se autorizará automáticamente para el ETL.</small>
          </p>

          {error && (
            <div className="error-message">
              <span>⚠️</span>
              <p>{error}</p>
            </div>
          )}

          <button
            onClick={handleGoogleLogin}
            disabled={loading}
            className="google-login-btn"
          >
            {loading ? (
              <>
                <div className="spinner"></div>
                <span>Iniciando sesión...</span>
              </>
            ) : (
              <>
                <svg width="20" height="20" viewBox="0 0 20 20">
                  <path fill="#4285F4" d="M19.6 10.23c0-.82-.1-1.42-.25-2.05H10v3.72h5.5c-.15.96-.74 2.31-2.04 3.22v2.45h3.16c1.89-1.73 2.98-4.3 2.98-7.34z"/>
                  <path fill="#34A853" d="M13.46 15.13c-.83.59-1.96 1-3.46 1-2.64 0-4.88-1.74-5.68-4.15H1.07v2.52C2.72 17.75 6.09 20 10 20c2.7 0 4.96-.89 6.62-2.42l-3.16-2.45z"/>
                  <path fill="#FBBC05" d="M3.99 10c0-.69.12-1.35.32-1.97V5.51H1.07A9.973 9.973 0 000 10c0 1.61.39 3.14 1.07 4.49l3.24-2.52c-.2-.62-.32-1.28-.32-1.97z"/>
                  <path fill="#EA4335" d="M10 3.88c1.88 0 3.13.81 3.85 1.48l2.84-2.76C14.96.99 12.7 0 10 0 6.09 0 2.72 2.25 1.07 5.51l3.24 2.52C5.12 5.62 7.36 3.88 10 3.88z"/>
                </svg>
                <span>Continuar con Google</span>
              </>
            )}
          </button>

          <div className="login-footer">
            <p>
              Al iniciar sesión, autorizas a SmartPharm a acceder a tu cuenta de Google
              y Gmail para el procesamiento de ofertas de laboratorios.
            </p>
          </div>
        </div>
      </div>

      <div className="login-background">
        <div className="circle circle-1"></div>
        <div className="circle circle-2"></div>
        <div className="circle circle-3"></div>
      </div>
    </div>
  );
}

export default Login;
