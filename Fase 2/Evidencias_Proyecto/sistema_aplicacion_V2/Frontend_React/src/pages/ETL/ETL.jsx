import { useState, useEffect } from 'react';
import { etlService, gmailAuthService } from '../../services/api';
import { useAuth } from '../../context/AuthContext';

function ETL() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState([]);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');
  const [gmailAuthenticated, setGmailAuthenticated] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [progress, setProgress] = useState(null);
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    loadData();
    checkGmailAuth();
  }, []);

  // Polling para progreso del ETL
  useEffect(() => {
    let intervalId;

    if (isRunning) {
      // Poll cada 500ms para actualizaciones en tiempo real
      intervalId = setInterval(async () => {
        try {
          const response = await etlService.getProgress();
          if (response.data.success) {
            if (response.data.running && response.data.progress) {
              setProgress(response.data.progress);
            } else {
              // ETL terminó
              setIsRunning(false);
              setProgress(response.data.progress);
              setLoading(false);

              // Recargar datos después de completar
              setTimeout(() => {
                loadData();
                setProgress(null);
              }, 3000);
            }
          }
        } catch (err) {
          console.error('Error checking progress:', err);
        }
      }, 500);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [isRunning]);

  const checkGmailAuth = async () => {
    try {
      setCheckingAuth(true);
      const response = await gmailAuthService.checkStatus();
      setGmailAuthenticated(response.data.authenticated);
    } catch (err) {
      console.error('Error checking Gmail auth:', err);
      setGmailAuthenticated(false);
    } finally {
      setCheckingAuth(false);
    }
  };

  const loadData = async () => {
    try {
      const [logsRes, statusRes] = await Promise.all([
        etlService.getLogs(),
        etlService.getStatus()
      ]);
      setLogs(logsRes.data.data || []);
      setStatus(statusRes.data.last_execution);
    } catch (err) {
      console.error('Error loading ETL data:', err);
    }
  };

  const handleRunETL = async () => {
    // Verificar autenticación antes de ejecutar
    if (!gmailAuthenticated) {
      setError('Debes autenticar Gmail primero antes de ejecutar el ETL.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setSuccessMessage('');
      setProgress(null);

      // Usar modo amplio (strict_mode=false) para buscar todos los correos con Excel/CSV
      const response = await etlService.runManual(2, false);

      if (response.data.success) {
        setSuccessMessage('✓ ETL iniciado. Buscando correos de Mediven/Socofar y mensajes con palabras clave (últimos 2 días)...');
        setIsRunning(true); // Iniciar polling de progreso
      }
    } catch (err) {
      const errorMsg = err.response?.data?.error || 'Error al ejecutar ETL';
      setError(errorMsg);
      setLoading(false);

      // Si el error es por falta de autenticación, actualizar estado
      if (errorMsg.includes('autenticado') || errorMsg.includes('Gmail')) {
        setGmailAuthenticated(false);
      }
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Sistema ETL</h1>
        <p className="text-gray-600">Descarga y procesa ofertas de laboratorios desde Gmail</p>
      </div>

      {/* Estado de Autenticación Gmail */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Autenticación de Gmail</h2>

        {checkingAuth ? (
          <div className="flex items-center text-gray-600">
            <svg className="animate-spin h-5 w-5 mr-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Verificando autenticación...
          </div>
        ) : gmailAuthenticated ? (
          <div className="flex items-center">
            <div className="flex-1">
              <div className="flex items-center text-green-600 mb-2">
                <svg className="h-5 w-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span className="font-semibold">Gmail autenticado correctamente</span>
              </div>
              <p className="text-sm text-gray-600">
                El sistema tiene acceso para leer correos de Gmail.
                <span className="block mt-1 text-xs text-gray-500">
                  ✓ Gmail se autorizó automáticamente al iniciar sesión con Google
                </span>
              </p>
            </div>
          </div>
        ) : (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center text-red-600 mb-2">
              <svg className="h-5 w-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <span className="font-semibold">Error de autenticación</span>
            </div>
            <p className="text-sm text-red-700 mb-2">
              Gmail no está autenticado. Por favor, cierra sesión y vuelve a iniciar sesión para autorizar Gmail automáticamente.
            </p>
            <p className="text-xs text-red-600">
              La autenticación de Gmail se realiza automáticamente al iniciar sesión con Google.
            </p>
          </div>
        )}
      </div>

      {/* Información de Automatización */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-6 mb-6">
        <div className="flex items-start gap-4">
          <div className="bg-purple-100 p-3 rounded-full">
            <svg className="h-6 w-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-purple-900 mb-2">Ejecución Automática Programada</h3>
            <p className="text-purple-800 mb-2">
              El ETL se ejecuta automáticamente <strong>cada 2 días a las 8:00 AM</strong> para mantener las ofertas actualizadas.
            </p>
            <p className="text-sm text-purple-700">
              También puedes ejecutarlo manualmente cuando lo necesites usando el botón a continuación.
            </p>
          </div>
        </div>
      </div>

      {/* Botón principal */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Ejecutar ETL Manualmente</h2>
        <p className="text-gray-600 mb-4">
          Busca correos de Mediven/Socofar y mensajes con palabras clave de ofertas de los últimos 2 días.
          Los archivos Excel y CSV adjuntos se procesan y las ofertas se cargan en la base de datos.
        </p>

        <button
          onClick={handleRunETL}
          disabled={loading || !gmailAuthenticated}
          className={`px-6 py-3 rounded-lg font-semibold text-white transition-colors ${
            loading || !gmailAuthenticated
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {loading ? (
            <span className="flex items-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Ejecutando ETL...
            </span>
          ) : (
            '🚀 Ejecutar ETL y Actualizar Precios'
          )}
        </button>

        {!gmailAuthenticated && !checkingAuth && (
          <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-yellow-800 font-semibold mb-2">⚠️ Debes autenticar Gmail antes de ejecutar el ETL</p>
            <p className="text-yellow-700 text-sm mt-2">
              💡 <strong>Importante:</strong> Se abrirá una ventana emergente con la autenticación de Google.
              Si no aparece, verifica que tu navegador permite ventanas emergentes para este sitio.
            </p>
          </div>
        )}

        {/* Barra de progreso en tiempo real */}
        {progress && isRunning && (
          <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <div>
                <p className="text-blue-900 font-semibold text-sm">Progreso del ETL</p>
                <p className="text-blue-700 text-xs">{progress.message}</p>
              </div>
              <div className="text-2xl font-bold text-blue-600">
                {progress.percentage}%
              </div>
            </div>
            <div className="w-full bg-blue-200 rounded-full h-4 overflow-hidden">
              <div
                className="bg-blue-600 h-4 transition-all duration-300 ease-out flex items-center justify-end pr-2"
                style={{ width: `${progress.percentage}%` }}
              >
                <span className="text-xs text-white font-medium">
                  {progress.percentage >= 10 && `${progress.percentage}%`}
                </span>
              </div>
            </div>
            <div className="mt-3 grid grid-cols-4 gap-2 text-xs">
              <div className="text-center">
                <p className="text-gray-600">Correos</p>
                <p className="font-semibold text-blue-900">{progress.stats?.emails_processed || 0}</p>
              </div>
              <div className="text-center">
                <p className="text-gray-600">Adjuntos</p>
                <p className="font-semibold text-blue-900">{progress.stats?.attachments_downloaded || 0}</p>
              </div>
              <div className="text-center">
                <p className="text-gray-600">Extraídas</p>
                <p className="font-semibold text-blue-900">{progress.stats?.offers_extracted || 0}</p>
              </div>
              <div className="text-center">
                <p className="text-gray-600">Insertadas</p>
                <p className="font-semibold text-green-600">{progress.stats?.offers_inserted || 0}</p>
              </div>
            </div>
          </div>
        )}

        {/* Mensaje de éxito al completar */}
        {progress && !isRunning && progress.stage === 'completado' && (
          <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center gap-2">
              <svg className="h-5 w-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <p className="text-green-800 font-semibold">ETL completado exitosamente</p>
            </div>
            <p className="text-green-700 text-sm mt-1">{progress.message}</p>
          </div>
        )}

        {successMessage && !progress && (
          <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="text-green-800">{successMessage}</p>
          </div>
        )}

        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">❌ {error}</p>
          </div>
        )}
      </div>

      {/* Estado último ETL */}
      {status && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Última Ejecución</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-600">Fecha</p>
              <p className="text-lg font-semibold">
                {new Date(status.fecha).toLocaleString('es-CL')}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Estado</p>
              <p className={`text-lg font-semibold ${status.exitoso ? 'text-green-600' : 'text-red-600'}`}>
                {status.exitoso ? '✓ Exitoso' : '✗ Falló'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Ofertas Insertadas</p>
              <p className="text-lg font-semibold text-blue-600">{status.ofertas_insertadas}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Duración</p>
              <p className="text-lg font-semibold">{status.duracion_segundos.toFixed(1)}s</p>
            </div>
          </div>
        </div>
      )}

      {/* Historial */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Historial de Ejecuciones</h2>

        {logs.length === 0 ? (
          <p className="text-gray-500">No hay registros de ejecuciones anteriores</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Fecha</th>
                  <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Estado</th>
                  <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Emails</th>
                  <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Adjuntos</th>
                  <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Extraídas</th>
                  <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Insertadas</th>
                  <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Duración</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id} className="border-t hover:bg-gray-50">
                    <td className="px-4 py-2 text-sm">
                      {new Date(log.fecha_ejecucion).toLocaleString('es-CL')}
                    </td>
                    <td className="px-4 py-2 text-sm">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${
                        log.exitoso ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {log.exitoso ? 'Exitoso' : 'Falló'}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-sm">{log.emails_procesados}</td>
                    <td className="px-4 py-2 text-sm">{log.adjuntos_descargados}</td>
                    <td className="px-4 py-2 text-sm">{log.ofertas_extraidas}</td>
                    <td className="px-4 py-2 text-sm text-blue-600 font-semibold">{log.ofertas_insertadas}</td>
                    <td className="px-4 py-2 text-sm">{log.duracion_segundos.toFixed(1)}s</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Información adicional */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">ℹ️ Criterios de Validación</h3>
        <div className="space-y-3">
          <div>
            <p className="font-semibold text-blue-900 mb-1">📧 Búsqueda de correos:</p>
            <ul className="list-disc list-inside text-blue-800 text-sm space-y-1 ml-4">
              <li>Busca correos de los últimos 2 días con adjuntos Excel/CSV</li>
              <li>Formatos aceptados: .xlsx, .xls, .csv</li>
            </ul>
          </div>

          <div>
            <p className="font-semibold text-blue-900 mb-1">✅ Correos aceptados:</p>
            <ul className="list-disc list-inside text-blue-800 text-sm space-y-1 ml-4">
              <li><strong>Dominios confiables:</strong> Mediven, Socofar (siempre se aceptan)</li>
              <li><strong>Palabras clave en asunto/cuerpo:</strong> Precio, Oferta, Laboratorio, Promoción, Lista, Descuento, Farmacia (singular/plural, mayúsculas/minúsculas)</li>
            </ul>
          </div>

          <div>
            <p className="font-semibold text-blue-900 mb-1">❌ Correos excluidos:</p>
            <ul className="list-disc list-inside text-blue-800 text-sm space-y-1 ml-4">
              <li>Correos enviados desde proyectosmartpharm2025@gmail.com</li>
              <li>Correos sin palabras clave ni de dominios confiables</li>
            </ul>
          </div>

          <div>
            <p className="font-semibold text-blue-900 mb-1">🔄 Proceso:</p>
            <ul className="list-disc list-inside text-blue-800 text-sm space-y-1 ml-4">
              <li>Extrae ofertas de los archivos validados</li>
              <li>Reescribe completamente la base de datos (elimina ofertas antiguas)</li>
              <li>Gmail se autoriza automáticamente al iniciar sesión</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ETL;
