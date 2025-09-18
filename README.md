Proyecto Capstone Duoc UC - Sede Antonio Varas
Ingeniería en Informática 2025
Descripción
SmartPharm CRM es una propuesta de negocio para desarrollar el primer sistema de gestión de clientes diseñado específicamente para farmacias pequeñas en Chile. El proyecto combina análisis financiero integral, plan de gestión de proyectos PMI, y desarrollo de MVP técnico como validación del concepto.
Problemática
Las farmacias pequeñas carecen de herramientas CRM especializadas que comprendan:

Patrones de compra de medicamentos crónicos
Estacionalidad de demanda farmacéutica (gripes en invierno, alergias en primavera)
Necesidades específicas de fidelización en el sector salud
Correlación con datos epidemiológicos públicos

Solución Propuesta
Sistema CRM especializado con tres componentes principales:

Segmentación de clientes farmacéuticos por tipo de medicamento y frecuencia
Análisis predictivo de demanda estacional correlacionado con datos de salud pública
Dashboard CRM con alertas especializadas para abandono de medicamentos crónicos

Equipo
RolNombreResponsabilidadLíder de ProyectoEnrique GarcíaAnálisis financiero, gestión PMI, coordinación generalValidador de MercadoDaniel AcevedoRequerimientos del sector (5+ años administrando farmacia)DesarrolladorBastian HartalMVP técnico, documentación de arquitectura
Estructura del Proyecto
Documentación de Negocio (70%)
docs/
├── business-plan/           # Business plan ejecutivo (20-25 páginas)
├── financial-analysis/      # Modelos ROI, VAN, TIR, proyecciones
├── project-management/      # Cronograma PMI, presupuesto, riesgos
└── funding-proposal/        # Estrategia de financiamiento
Componente Técnico (30%)
src/
├── backend/                 # API Python para análisis de datos
├── frontend/               # Dashboard Angular con visualizaciones
├── data/                   # Datos históricos de farmacia piloto
└── analysis/               # Scripts de análisis predictivo
Cronograma de Desarrollo
SemanasFaseEntregables1-2Análisis de MercadoInvestigación sectorial, requerimientos3-5Propuesta FinancieraBusiness plan, modelos ROI/VAN/TIR6-7Gestión de ProyectosCronograma PMI, presupuesto, riesgos8-10MVP Técnico3 funcionalidades, documentación
MVP Técnico - 3 Funcionalidades
1. Segmentación de Clientes

Clasificación automática por medicamentos crónicos vs agudos
Análisis de frecuencia de compra
Identificación de clientes de alto valor

2. Predicción Estacional

Análisis de ventas históricas por temporada
Correlación básica con datos del Ministerio de Salud
Alertas de picos de demanda anticipados

3. Dashboard CRM

Visualización de patrones de clientes
Alertas por abandono de medicamentos habituales
Recomendaciones de stock estacional

Stack Tecnológico

Backend: Python (Django, FastAPI, Pandas)
Frontend: Angular
Base de Datos: PostgreSQL
Análisis: Python (análisis estadístico básico)
Visualización: Chart.js, dashboard web
Cloud: Google Cloud Platform (herramientas gratuitas)

Validación con Datos Reales

Farmacia piloto: Acceso a 3+ años de datos históricos
Usuario real: Daniel Acevedo (administrador farmacia, miembro del equipo)
Datos disponibles: 15,000+ transacciones, 2,800+ clientes únicos
Validación continua: Testing semanal con usuario final

Instalación (MVP Técnico)
Prerrequisitos
bashPython 3.8+
Node.js 16+
PostgreSQL 12+
Setup Backend
bashcd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
Setup Frontend
bashcd frontend
npm install
ng serve
Variables de Entorno
bash# .env
DATABASE_URL=postgresql://user:password@localhost:5432/smartpharm_db
SECRET_KEY=your-secret-key
DEBUG=True
Entregables Académicos
Documentación de Negocio (70%):

 Business Plan Ejecutivo (20-25 páginas)
 Análisis Financiero Completo (ROI, VAN, TIR)
 Plan de Gestión de Proyectos (PMI)
 Propuesta de Financiamiento
 Presentación Ejecutiva (Pitch Deck)

Componente Técnico (30%):

 MVP con 3 funcionalidades core
 Documentación técnica de arquitectura
 Análisis de datos validado con farmacia piloto
 Plan de escalamiento tecnológico

Diferenciación

Especialización sectorial: Único CRM diseñado para farmacias vs soluciones genéricas
Conocimiento farmacéutico: Comprende medicamentos crónicos y estacionalidad
Validación real: Desarrollo con datos y feedback de farmacia real
Enfoque académico: Balance entre viabilidad comercial y factibilidad técnica

Estado del Proyecto
🟡 En Desarrollo - Proyecto Capstone académico con enfoque en propuesta de negocio
Sprint Actual

Análisis de mercado farmacéutico chileno
Desarrollo de modelos financieros iniciales
Setup de arquitectura básica para MVP

Métricas de Éxito Académico

Viabilidad financiera: VAN positivo en análisis conservador
Factibilidad técnica: MVP funcional con datos reales
Calidad de propuesta: Business plan presentable a inversionistas
Gestión de proyectos: Cronograma y presupuesto detallados y realistas

Limitaciones Reconocidas

Alcance académico: 10 semanas para propuesta completa + MVP
Validación limitada: Una farmacia piloto, no múltiples establecimientos
Enfoque educativo: Prototipo funcional, no solución comercial lista

Contribuciones

Fork el repositorio
Crea una rama feature (git checkout -b feature/nueva-funcionalidad)
Commit tus cambios (git commit -am 'Agrega nueva funcionalidad')
Push a la rama (git push origin feature/nueva-funcionalidad)
Abre un Pull Request

Licencia
MIT License - ver LICENSE para detalles

Proyecto Capstone Duoc UC 2025
Propuesta de negocio para CRM especializado en farmacias con validación técnica mediante MVP funcional
Contacto del Equipo:

Enrique García (Líder): LinkedIn
Daniel Acevedo (Validador): Administrador Farmacia
Bastian Hartal (Desarrollador): Experiencia farmacéutica

Documentación Adicional

Plan de Proyecto APT
Análisis de Mercado
Arquitectura Técnica
Guía de Contribución
