import { createContext, useState, useContext, useEffect } from 'react';
import { authService } from '../services/api';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth debe usarse dentro de AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Verificar sesión al cargar la app
  useEffect(() => {
    checkSession();
  }, []);

  const checkSession = async () => {
    try {
      const response = await authService.checkSession();
      if (response.data.logged_in) {
        setUser(response.data.user);
        setIsAuthenticated(true);
      } else {
        setUser(null);
        setIsAuthenticated(false);
      }
    } catch (error) {
      console.error('Error checking session:', error);
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  const login = async () => {
    try {
      console.log('📞 Llamando a /api/auth/login/start/...');
      const response = await authService.startLogin();
      console.log('📦 Respuesta del backend:', response.data);

      if (response.data.success && response.data.auth_url) {
        const width = 600;
        const height = 700;
        const left = window.screen.width / 2 - width / 2;
        const top = window.screen.height / 2 - height / 2;

        console.log('🔓 Abriendo popup de Google OAuth...');
        const popup = window.open(
          response.data.auth_url,
          'GoogleLogin',
          `width=${width},height=${height},left=${left},top=${top}`
        );

        if (!popup) {
          throw new Error('Popup bloqueado. Permite ventanas emergentes para localhost.');
        }

        console.log('✅ Popup abierto, monitoreando sesión en backend...');

        // Esperar resultado del popup
        return new Promise((resolve, reject) => {
          let loginCompleted = false;

          // Listener para postMessage (si funciona)
          const handleMessage = (event) => {
            const allowedOrigins = ['http://localhost', 'http://localhost:8000', 'http://127.0.0.1', 'http://127.0.0.1:8000'];
            if (!allowedOrigins.includes(event.origin)) {
              return;
            }

            console.log('📩 Mensaje postMessage recibido:', event.data);

            if (event.data.type === 'LOGIN_SUCCESS' && !loginCompleted) {
              console.log('✅ Login exitoso (vía postMessage):', event.data.user.email);
              loginCompleted = true;
              clearInterval(sessionPolling);
              window.removeEventListener('message', handleMessage);
              setUser(event.data.user);
              setIsAuthenticated(true);
              resolve(event.data.user);
            } else if (event.data.type === 'LOGIN_ERROR' && !loginCompleted) {
              console.error('❌ Error en login (vía postMessage):', event.data.message);
              loginCompleted = true;
              clearInterval(sessionPolling);
              window.removeEventListener('message', handleMessage);
              reject(new Error(event.data.message || 'Error al iniciar sesión'));
            }
          };

          window.addEventListener('message', handleMessage);

          // Polling al backend cada 1 segundo para detectar sesión inmediatamente
          console.log('🔄 Iniciando polling de sesión cada 1 segundo...');
          const sessionPolling = setInterval(async () => {
            if (loginCompleted) return;

            try {
              const response = await authService.checkSession();

              if (response.data.logged_in) {
                console.log('✅ Sesión detectada en backend:', response.data.user.email);
                loginCompleted = true;
                clearInterval(sessionPolling);
                window.removeEventListener('message', handleMessage);
                setUser(response.data.user);
                setIsAuthenticated(true);
                resolve(response.data.user);
              }
            } catch (error) {
              console.debug('⏳ Esperando login...');
            }
          }, 1000); // Verificar cada 1 segundo

          // Timeout máximo de 60 segundos (1 minuto)
          setTimeout(() => {
            if (loginCompleted) return;

            console.warn('⏱️ Timeout después de 60 segundos');
            clearInterval(sessionPolling);
            window.removeEventListener('message', handleMessage);
            reject(new Error('Tiempo agotado. Por favor intenta de nuevo.'));
          }, 60000);
        });
      }
    } catch (error) {
      console.error('Error during login:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
      setUser(null);
      setIsAuthenticated(false);
    } catch (error) {
      console.error('Error during logout:', error);
      // Cerrar sesión localmente aunque falle el backend
      setUser(null);
      setIsAuthenticated(false);
    }
  };

  const value = {
    user,
    loading,
    isAuthenticated,
    login,
    logout,
    checkSession
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
