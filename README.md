# SmartPharm CRM - Sistema Especializado para Farmacias

**Proyecto Capstone Duoc UC - Grupo 5**  
**Duración:** 10 semanas académicas  
**Enfoque:** 70% Propuesta Financiera y Gestión de Proyectos, 30% MVP Técnico

## Descripción

SmartPharm CRM es una propuesta de negocio para desarrollar el primer sistema de gestión de clientes diseñado específicamente para farmacias pequeñas en Chile. El proyecto combina análisis financiero integral, plan de gestión de proyectos, y desarrollo de MVP técnico como validación del concepto.

## Problema

Las farmacias pequeñas carecen de herramientas CRM especializadas que comprendan:
- Patrones de compra de medicamentos crónicos
- Estacionalidad de demanda farmacéutica (gripes en invierno, alergias en primavera)
- Necesidades específicas de fidelización en el sector salud
- Correlación con datos epidemiológicos públicos

## Solución Propuesta

Sistema CRM especializado con tres componentes principales:
1. **Segmentación de clientes farmacéuticos** por tipo de medicamento y frecuencia
2. **Análisis predictivo de demanda estacional** correlacionado con datos de salud pública
3. **Dashboard CRM con alertas especializadas** para abandono de medicamentos crónicos

## Equipo

| Rol | Nombre | Responsabilidad |
|-----|---------|-----------------|
| **Líder de Proyecto** | Enrique García | Análisis financiero, gestión PMI, coordinación general |
| **Validador de Mercado** | Daniel Acevedo | Requerimientos del sector (5+ años administrando farmacia) |
| **Desarrollador** | Bastian Hartal | MVP técnico, documentación de arquitectura |

## Estructura del Proyecto

### Documentación de Negocio (70%)
```
docs/
├── business-plan/           # Business plan ejecutivo (20-25 páginas)
├── financial-analysis/      # Modelos ROI, VAN, TIR, proyecciones
├── project-management/      # Cronograma PMI, presupuesto, riesgos
└── funding-proposal/        # Estrategia de financiamiento
```

### Componente Técnico (30%)
```
src/
├── backend/                 # API Python para análisis de datos
├── frontend/               # Dashboard React con visualizaciones
├── data/                   # Datos históricos de farmacia piloto
└── analysis/               # Scripts de análisis predictivo
```

## Cronograma de Desarrollo

| Semanas | Fase | Entregables |
|---------|------|-------------|
| 1-2 | Análisis de Mercado | Investigación sectorial, requerimientos |
| 3-5 | Propuesta Financiera | Business plan, modelos ROI/VAN/TIR |
| 6-7 | Gestión de Proyectos | Cronograma PMI, presupuesto, riesgos |
| 8-10 | MVP Técnico | 3 funcionalidades, documentación |

## MVP Técnico - 3 Funcionalidades

### 1. Segmentación de Clientes
- Clasificación automática por medicamentos crónicos vs agudos
- Análisis de frecuencia de compra
- Identificación de clientes de alto valor

### 2. Predicción Estacional
- Análisis de ventas históricas por temporada
- Correlación básica con datos del Ministerio de Salud
- Alertas de picos de demanda anticipados

### 3. Dashboard CRM
- Visualización de patrones de clientes
- Alertas por abandono de medicamentos habituales
- Recomendaciones de stock estacional

## Stack Tecnológico

- **Backend:** Python (FastAPI, Pandas)
- **Frontend:** React/Next.js
- **Base de Datos:** PostgreSQL
- **Análisis:** Python (análisis estadístico básico)
- **Visualización:** Chart.js, dashboard web

## Validación con Datos Reales

- **Farmacia piloto:** Acceso a 3+ años de datos históricos
- **Usuario real:** Daniel Acevedo (administrador farmacia, miembro del equipo)
- **Datos disponibles:** 15,000+ transacciones, 2,800+ clientes únicos
- **Validación continua:** Testing semanal con usuario final

## Entregables Académicos

### Documentación de Negocio (70%):
- [ ] Business Plan Ejecutivo (20-25 páginas)
- [ ] Análisis Financiero Completo (ROI, VAN, TIR)
- [ ] Plan de Gestión de Proyectos (PMI)
- [ ] Propuesta de Financiamiento
- [ ] Presentación Ejecutiva (Pitch Deck)

### Componente Técnico (30%):
- [ ] MVP con 3 funcionalidades core
- [ ] Documentación técnica de arquitectura
- [ ] Análisis de datos validado con farmacia piloto
- [ ] Plan de escalamiento tecnológico

## Diferenciación

- **Especialización sectorial:** Único CRM diseñado para farmacias vs soluciones genéricas
- **Conocimiento farmacéutico:** Comprende medicamentos crónicos y estacionalidad
- **Validación real:** Desarrollo con datos y feedback de farmacia real
- **Enfoque académico:** Balance entre viabilidad comercial y factibilidad técnica

## Instalación (MVP Técnico)

### Prerrequisitos
```bash
Python 3.8+
Node.js 16+
PostgreSQL 12+
```

### Setup Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

### Setup Frontend
```bash
cd frontend
npm install
npm run dev
```

## Estado del Proyecto

🟡 **En Desarrollo** - Proyecto Capstone académico con enfoque en propuesta de negocio

### Sprint Actual
- Análisis de mercado farmacéutico chileno
- Desarrollo de modelos financieros iniciales
- Setup de arquitectura básica para MVP

## Métricas de Éxito Académico

- **Viabilidad financiera:** VAN positivo en análisis conservador
- **Factibilidad técnica:** MVP funcional con datos reales
- **Calidad de propuesta:** Business plan presentable a inversionistas
- **Gestión de proyectos:** Cronograma y presupuesto detallados y realistas

## Limitaciones Reconocidas

- **Alcance académico:** 10 semanas para propuesta completa + MVP
- **Validación limitada:** Una farmacia piloto, no múltiples establecimientos
- **Enfoque educativo:** Prototipo funcional, no solución comercial lista

## Licencia

MIT License - ver [LICENSE](LICENSE) para detalles

---

**Proyecto Capstone Duoc UC 2025**  
*Propuesta de negocio para CRM especializado en farmacias con validación técnica mediante MVP funcional*

**Contacto del Equipo:**  
- Enrique García (Líder): [LinkedIn](https://linkedin.com/in/enrique-g-2462171b4)
- Daniel Acevedo (Validador): Administrador Farmacia
- Bastian Hartal (Desarrollador): Experiencia farmacéutica

## Contribuciones

1. Fork el repositorio
2. Crea una rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request
