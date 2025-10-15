# SmartPharm - Roadmap de Implementación

## Proyecto: Sistema Inteligente de Gestión Farmacéutica

### Estado Actual: Frontend React Implementado + Backend Django Base

---

## Casos de Uso Implementados (Versión Actual)

### 1. Dashboard Interactivo
- ✅ Visualización de ventas totales y del mes
- ✅ Gráficos de ventas mensuales (Recharts)
- ✅ Top 10 productos más vendidos
- ✅ Actualización automática cada 30 segundos
- ✅ Estadísticas de productos en stock y clientes activos

### 2. Gestión de Inventario
- ✅ Lista completa de productos con código, descripción, cantidad
- ✅ Filtros por nivel de stock (bajo, normal, crítico)
- ✅ Búsqueda por código, descripción o categoría
- ✅ Alertas visuales para productos con bajo stock
- ✅ Indicadores de estado por color

### 3. Gestión de Clientes
- ✅ Clasificación automática: Frecuentes (≥5 compras) y Normales (<5 compras)
- ✅ Vista de historial de compras por cliente
- ✅ Filtros y búsqueda avanzada
- ✅ Preparado para envío de correos masivos a clientes frecuentes

### 4. Sugerencias de Compra Inteligente
- ✅ UI para sugerencias por bajo stock
- ✅ UI para sugerencias estacionales (Machine Learning)
- ✅ UI para sugerencias epidemiológicas (MINSAL)
- ✅ Carga de ofertas de laboratorios (ETL de Excel/PDF)
- ✅ Generación de órdenes de compra

---

## Casos de Uso Futuros (Por Implementar)

### CASO DE USO #1: Machine Learning - Predicción de Demanda

**Objetivo:** Predecir bajo stock y sugerencias por cambio de estaciones del año

#### Implementación Sugerida:

**Tecnologías:**
- Python: scikit-learn, pandas, numpy
- Modelos: ARIMA, Prophet (Facebook), LSTM (redes neuronales)

**Pasos:**
1. **Recopilación de Datos Históricos**
   - Crear tabla `HistoricoVentas` con datos de al menos 1-2 años
   - Incluir: fecha, producto, cantidad vendida, estación, temperatura, eventos

2. **Feature Engineering**
   ```python
   # Características estacionales
   - Mes del año (1-12)
   - Estación (primavera, verano, otoño, invierno)
   - Días festivos/fines de semana
   - Promedio móvil de ventas (7, 30, 90 días)
   - Tendencias (creciente, estable, decreciente)
   ```

3. **Modelo de Predicción**
   ```python
   # Ejemplo con Prophet
   from prophet import Prophet

   # Entrenar modelo por producto/categoría
   def predecir_demanda(producto_id, dias_futuro=30):
       # Obtener histórico
       df = obtener_historico(producto_id)
       model = Prophet()
       model.fit(df)

       # Predecir
       future = model.make_future_dataframe(periods=dias_futuro)
       forecast = model.predict(future)

       return forecast
   ```

4. **Integración con Django**
   - Crear comando: `python manage.py generar_predicciones`
   - Ejecutar diariamente con celery/cron
   - Guardar en modelo `SugerenciaCompra` con tipo='ml'

**Confianza del Modelo:**
- Almacenar métricas: RMSE, MAE, MAPE
- Mostrar en frontend como porcentaje de confianza

---

### CASO DE USO #2: ETL - Procesamiento de Ofertas de Laboratorios

**Objetivo:** Automatizar lectura, limpieza e inserción de ofertas desde Excel/PDF cada 3 días

#### Implementación Sugerida:

**Tecnologías:**
- pandas, openpyxl (Excel)
- PyPDF2, tabula-py (PDF)
- celery (automatización)

**Pasos:**

1. **Configuración de Correo**
   ```python
   # settings.py
   EMAIL_BACKEND = 'django.core.mail.backends.imap.EmailBackend'
   EMAIL_HOST = 'imap.gmail.com'
   EMAIL_USE_TLS = True
   ```

2. **Script de Lectura de Correos**
   ```python
   import imaplib
   import email

   def leer_correos_ofertas():
       mail = imaplib.IMAP4_SSL('imap.gmail.com')
       mail.login('farmacia@ejemplo.com', 'password')
       mail.select('inbox')

       # Buscar correos con adjuntos
       _, data = mail.search(None, 'UNSEEN', 'SUBJECT', '"Oferta"')

       for num in data[0].split():
           _, msg = mail.fetch(num, '(RFC822)')
           for part in msg:
               if part.get_content_type() in ['application/pdf', 'application/vnd.ms-excel']:
                   procesar_archivo(part.get_payload(decode=True))
   ```

3. **Procesamiento ETL**
   ```python
   import pandas as pd

   def procesar_excel(archivo):
       df = pd.read_excel(archivo)

       # Limpieza
       df = df.dropna(subset=['producto', 'precio'])
       df['precio'] = df['precio'].str.replace('$', '').astype(float)

       # Transformación
       for _, row in df.iterrows():
           OfertaLaboratorio.objects.create(
               proveedor=obtener_proveedor(row['laboratorio']),
               producto=obtener_producto(row['codigo']),
               precio_oferta=row['precio_oferta'],
               descuento_porcentaje=calcular_descuento(row),
               fecha_vigencia=row['vigencia'],
               archivo_origen=archivo.name
           )
   ```

4. **Automatización con Celery**
   ```python
   # tasks.py
   from celery import shared_task

   @shared_task
   def procesar_ofertas_programado():
       leer_correos_ofertas()
       generar_sugerencias_compra()

   # Ejecutar cada 3 días
   # celerybeat_schedule: {'procesar-ofertas': {..., 'schedule': crontab(hour=0, minute=0, day_of_week='*/3')}}
   ```

---

### CASO DE USO #3: Integración con API MINSAL

**Objetivo:** Obtener alertas epidemiológicas actuales y recomendar medicamentos

#### Implementación Sugerida:

**API MINSAL:**
- URL: https://api.minsal.cl/ (verificar disponibilidad)
- Alternativa: Web scraping de informes públicos

**Pasos:**

1. **Consulta API/Web Scraping**
   ```python
   import requests
   from bs4 import BeautifulSoup

   def obtener_alertas_minsal():
       # Opción 1: API
       response = requests.get('https://api.minsal.cl/alertas')
       datos = response.json()

       # Opción 2: Web Scraping
       url = 'https://www.minsal.cl/category/noticias/page/1/'
       response = requests.get(url)
       soup = BeautifulSoup(response.content, 'html.parser')

       # Extraer información
       alertas = []
       for articulo in soup.find_all('article'):
           if 'influenza' in articulo.text.lower() or 'alerta' in articulo.text.lower():
               alertas.append({
                   'titulo': articulo.find('h2').text,
                   'fecha': extraer_fecha(articulo),
                   'contenido': articulo.find('p').text
               })

       return alertas
   ```

2. **Procesamiento NLP**
   ```python
   from sklearn.feature_extraction.text import TfidfVectorizer

   # Mapeo de enfermedades -> medicamentos
   MEDICAMENTOS_MAP = {
       'influenza': ['Oseltamivir', 'Paracetamol', 'Ibuprofeno'],
       'covid': ['Paracetamol', 'Azitromicina'],
       'alergia': ['Loratadina', 'Cetirizina', 'Budesonida'],
   }

   def analizar_alerta(texto):
       # Detectar enfermedad mencionada
       for enfermedad, medicamentos in MEDICAMENTOS_MAP.items():
           if enfermedad in texto.lower():
               return enfermedad, medicamentos
   ```

3. **Generación Automática de Sugerencias**
   ```python
   def generar_sugerencias_epidemiologicas():
       alertas = obtener_alertas_minsal()

       for alerta in alertas:
           enfermedad, medicamentos = analizar_alerta(alerta['contenido'])

           for med_nombre in medicamentos:
               producto = Producto.objects.get(descripcion__icontains=med_nombre)

               SugerenciaCompra.objects.create(
                   producto=producto,
                   tipo='epidemiologico',
                   cantidad_sugerida=calcular_demanda_estimada(producto, alerta),
                   prioridad='alta',
                   razon=f"Alerta MINSAL: {enfermedad}",
                   fuente_datos='MINSAL Chile'
               )
   ```

---

### CASO DE USO #4: Envío Automático de Correos a Clientes Frecuentes

**Objetivo:** Enviar ofertas personalizadas a clientes con >5 compras

#### Implementación Sugerida:

**Tecnologías:**
- Django Email + HTML Templates
- Celery para envío asíncrono

**Pasos:**

1. **Template HTML**
   ```html
   <!-- templates/email/oferta_cliente.html -->
   <!DOCTYPE html>
   <html>
   <body>
       <h1>Hola {{ cliente.nombre }},</h1>
       <p>Tenemos ofertas especiales para ti:</p>
       <ul>
       {% for oferta in ofertas %}
           <li>{{ oferta.producto.descripcion }} - <strong>{{ oferta.descuento_porcentaje }}% OFF</strong></li>
       {% endfor %}
       </ul>
       <a href="{{ link_farmacia }}">Ver más ofertas</a>
   </body>
   </html>
   ```

2. **Lógica de Envío**
   ```python
   from django.core.mail import send_mail
   from django.template.loader import render_to_string

   def enviar_ofertas_clientes_frecuentes():
       # Obtener clientes frecuentes
       clientes_frecuentes = Cliente.objects.annotate(
           total_compras=Count('ventas')
       ).filter(total_compras__gte=5)

       # Obtener ofertas vigentes
       ofertas = OfertaLaboratorio.objects.filter(
           fecha_vigencia__gte=timezone.now().date(),
           activa=True
       )[:10]

       for cliente in clientes_frecuentes:
           html_content = render_to_string('email/oferta_cliente.html', {
               'cliente': cliente,
               'ofertas': ofertas,
               'link_farmacia': 'https://smartpharm.cl'
           })

           send_mail(
               subject='Ofertas Exclusivas para Ti',
               message='',
               from_email='ofertas@smartpharm.cl',
               recipient_list=[cliente.correo],
               html_message=html_content
           )
   ```

3. **Registro y Seguimiento**
   ```python
   class EnvioEmail(models.Model):
       cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
       campana = models.ForeignKey(ConfiguracionEmail, on_delete=models.CASCADE)
       fecha_envio = models.DateTimeField(auto_now_add=True)
       abierto = models.BooleanField(default=False)
       fecha_apertura = models.DateTimeField(null=True)
       clic_enlace = models.BooleanField(default=False)
   ```

---

## Arquitectura Técnica Propuesta

### Backend (Django)
```
SmartPharm/
├── core/
│   ├── models.py (nuevos modelos de models_extended.py)
│   ├── views.py
│   ├── serializers.py
│   ├── ml/
│   │   ├── prediccion_demanda.py
│   │   ├── analisis_estacional.py
│   │   └── entrenar_modelos.py
│   ├── etl/
│   │   ├── procesar_excel.py
│   │   ├── procesar_pdf.py
│   │   └── leer_correos.py
│   ├── minsal/
│   │   ├── api_client.py
│   │   └── web_scraper.py
│   └── management/commands/
│       ├── entrenar_ml.py
│       ├── procesar_ofertas.py
│       ├── actualizar_minsal.py
│       └── enviar_emails.py
└── requirements.txt (actualizar)
```

### Dependencias Python Adicionales
```txt
# Machine Learning
scikit-learn==1.3.0
prophet==1.1.4
pandas==2.0.3
numpy==1.24.3

# ETL
openpyxl==3.1.2
PyPDF2==3.0.1
tabula-py==2.7.0

# Web Scraping
beautifulsoup4==4.12.2
requests==2.31.0

# Tareas Asíncronas
celery==5.3.1
redis==4.6.0

# Email
django-email-extras==0.3.4
```

### Frontend (React)
- Ya implementado con Vite, React Router, Recharts
- Preparado para conectar con nuevos endpoints API

---

## Timeline Sugerido

### Fase 1 (Semanas 1-2): Modelos y Backend Core
- [ ] Integrar modelos extendidos a core/models.py
- [ ] Crear migraciones y aplicarlas
- [ ] Implementar serializers y views REST
- [ ] Poblar datos de prueba

### Fase 2 (Semanas 3-4): Machine Learning
- [ ] Recopilar/simular datos históricos
- [ ] Implementar modelo de predicción con Prophet
- [ ] Crear comando entrenar_ml
- [ ] Integrar con SugerenciaCompra

### Fase 3 (Semanas 5-6): ETL y Ofertas
- [ ] Implementar lectura de correos
- [ ] Crear parsers Excel/PDF
- [ ] Automatizar con Celery (cada 3 días)
- [ ] Validar y limpiar datos

### Fase 4 (Semanas 7-8): API MINSAL y Sugerencias
- [ ] Conectar con API/scraping MINSAL
- [ ] Implementar análisis NLP básico
- [ ] Generar sugerencias automáticas
- [ ] Actualización diaria

### Fase 5 (Semanas 9-10): Sistema de Emails
- [ ] Crear templates HTML
- [ ] Implementar envío masivo
- [ ] Sistema de tracking (aperturas/clics)
- [ ] Panel de analíticas

### Fase 6 (Semanas 11-12): Testing e Integración
- [ ] Pruebas unitarias
- [ ] Pruebas de integración
- [ ] Optimización de performance
- [ ] Documentación final

---

## Comandos Útiles

### Ejecutar Frontend
```bash
cd smartpharm-frontend
npm run dev
```

### Ejecutar Backend
```bash
python manage.py runserver
```

### Crear Migraciones (cuando agregues modelos)
```bash
python manage.py makemigrations
python manage.py migrate
```

### Comandos Futuros (cuando se implementen)
```bash
# ML
python manage.py entrenar_ml --producto all

# ETL
python manage.py procesar_ofertas --archivo ofertas.xlsx

# MINSAL
python manage.py actualizar_minsal

# Emails
python manage.py enviar_emails --campana clientes_frecuentes
```

---

## Notas Importantes

1. **CORS:** Configurar en Django para permitir requests desde React (localhost:5173)
2. **Seguridad:** Usar variables de entorno para API keys, contraseñas de email
3. **Datos de Prueba:** Crear fixtures para desarrollo
4. **Monitoreo:** Implementar logging para ETL y ML
5. **Backup:** Programar backups diarios de PostgreSQL

---

**Última actualización:** 14 de octubre, 2025
**Versión:** 1.0 - Base Implementada
