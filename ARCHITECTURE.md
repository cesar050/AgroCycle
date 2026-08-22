# Decisiones de Arquitectura — AgroCycle

Este documento registra las decisiones técnicas significativas tomadas durante
el diseño e implementación de AgroCycle, con su justificación y las alternativas
consideradas. Formato ADR (Architecture Decision Record) simplificado.

---

## ADR-001 — Clean Architecture con cuatro capas estrictas

**Estado:** Adoptado  
**Fecha:** 2026-05

### Decisión
El backend sigue Clean Architecture con capas en este orden de dependencia: 
domain → application → infrastructure → interfaces

La capa `domain` no conoce a ninguna otra. La capa `application` solo conoce
a `domain`. `infrastructure` implementa los contratos de `domain`. `interfaces`
orquesta casos de uso desde las rutas Flask.

### Justificación
AgroCycle tiene un núcleo de negocio complejo (balance hídrico FAO-56, modelo
predictivo, geoespacial) que debe estar completamente desacoplado de Flask,
PostgreSQL y las APIs externas. Si mañana se cambia Open-Meteo por otra API
climática, solo cambia la capa de infraestructura.

### Rechazado
- MVC tradicional con Flask-SQLAlchemy directo en las rutas: demasiado acoplado
  para un sistema con 69 casos de uso y modelo predictivo intercambiable.
- Microservicios: innecesario para un equipo unipersonal en fase de validación.
  La Clean Architecture permite extraer microservicios en el futuro si el
  crecimiento lo requiere.

---

## ADR-002 — Monolito modular en lugar de microservicios

**Estado:** Adoptado  
**Fecha:** 2026-05

### Decisión
AgroCycle es un monolito modular. Todos los módulos corren en un único proceso
Flask, organizados en directorios independientes bajo `application/use_cases/`.

### Justificación
- Equipo unipersonal con deadline académico definido
- La primera temporada de validación tendrá un solo agricultor real
- La Clean Architecture ya garantiza el desacoplamiento necesario para extraer
  microservicios en el futuro sin rediseñar el sistema
- Shopify y Stack Overflow manejan millones de usuarios con monolitos bien
  construidos

### Rechazado
- Microservicios desde el inicio: introduce complejidad de red, orquestación
  con Kubernetes y consistencia de datos distribuida que no se justifica en
  esta etapa.

---

## ADR-003 — PostgreSQL + PostGIS para datos geoespaciales

**Estado:** Adoptado  
**Fecha:** 2026-05

### Decisión
Los polígonos de fincas, lotes y parcelas se almacenan como tipo `GEOMETRY(POLYGON, 4326)`
en PostgreSQL con la extensión PostGIS. Se usa índice GIST sobre la columna
de geometría.

### Justificación
Los terrenos agrícolas del sur del Ecuador son irregulares y montañosos. PostGIS
permite calcular superficie exacta con `ST_Area`, centroide con `ST_Centroid`
para consultas climáticas, y verificar superposiciones con `ST_Overlaps`. La
tolerancia de 10m con `ST_Buffer` compensa imprecisiones del dibujo manual.

### Rechazado
- Almacenar coordenadas como columnas `lat/lon` en tabla plana: pierde toda la
  inteligencia geográfica y requiere cálculos manuales en Python.
- MongoDB con GeoJSON: rompe la consistencia transaccional necesaria para el
  Unit of Work pattern.

---

## ADR-004 — Estimación sin sensores IoT

**Estado:** Adoptado  
**Fecha:** 2026-05

### Decisión
El indicador de humedad del suelo se calcula combinando datos de APIs externas
gratuitas (Open-Meteo) con características del terreno registradas por el
agricultor, usando la ecuación de evapotranspiración Penman-Monteith (FAO-56)
y el modelo de producción FAO-33. No se requieren sensores físicos.

### Justificación
Los agricultores de Bramaderos no pueden costear sensores IoT. La zona no
tiene infraestructura de conectividad confiable en campo. La aproximación
basada en datos indirectos es suficientemente útil para tomar decisiones
de riego aunque tenga margen de error.

### Rechazado
- Sensores IoT: fuera del alcance económico y técnico del usuario objetivo.
- Imágenes satelitales de pago (Planet Labs): costo prohibitivo para la etapa
  inicial. Planificado para v2.0.0 con Sentinel Hub si el proyecto obtiene
  financiamiento externo.

---

## ADR-005 — Open-Meteo como fuente climática principal

**Estado:** Adoptado  
**Fecha:** 2026-05

### Decisión
Open-Meteo es la API meteorológica principal para datos históricos (desde 1940)
y pronóstico a 16 días. No requiere API key ni tiene costo.

### Justificación
Open-Meteo tiene cobertura global con resolución de 1km, datos históricos que
permiten pre-entrenar el modelo predictivo antes de la primera temporada real,
y es completamente gratuita lo que garantiza la sostenibilidad del sistema.

### Alternativas evaluadas
- Tomorrow.io: mayor precisión por coordenada exacta, pero de pago (~150 USD/mes).
  Planificado como upgrade si el proyecto obtiene financiamiento.
- OpenWeatherMap: sin datos históricos suficientes para entrenar el modelo.

---

## ADR-006 — Estrategia de modelo predictivo en tres fases

**Estado:** Adoptado  
**Fecha:** 2026-06

### Decisión
El motor predictivo evoluciona en tres fases:
1. **FAO-33 + Penman-Monteith:** antes de datos reales propios
2. **Ridge Regression (scikit-learn):** con datos de la primera temporada real
3. **Random Forest con aprendizaje incremental:** con múltiples temporadas

El sistema implementa versionado de modelos. Un modelo de menor precisión nunca
reemplaza a uno de mayor precisión aunque el reentrenamiento sea más reciente.

### Justificación
AgroCycle solo tiene una temporada agrícola por año en la zona de validación.
No es posible tener suficientes datos para ML desde el inicio. Las ecuaciones
FAO son la mejor aproximación disponible con datos indirectos mientras se
acumula el historial real.

---

## ADR-007 — Celery + Redis para procesamiento asíncrono

**Estado:** Adoptado  
**Fecha:** 2026-06

### Decisión
Las operaciones pesadas se ejecutan en workers Celery con Redis como broker:
- Consultas a Open-Meteo y OpenTopoData
- Recálculo dinámico de estimaciones de producción
- Generación de reportes PDF con WeasyPrint
- Reentrenamiento del modelo predictivo al cierre de temporada

### Justificación
El agricultor no debe esperar mientras el sistema consulta APIs externas o
recalcula el modelo. Flask responde inmediatamente con 202 Accepted y Celery
procesa en segundo plano. Esto es crítico para la experiencia de usuario en
conexiones lentas de zonas rurales.

---

## ADR-008 — SVG propio para el mapa de la finca

**Estado:** Adoptado  
**Fecha:** 2026-06

### Decisión
La visualización del mapa finca→lote→parcela usa un renderer SVG propio con
proyección geográfica real, zoom/pan y colores por etapa fenológica. Leaflet
se usa exclusivamente para dibujar polígonos nuevos sobre tiles satelitales.

### Justificación
El mapa SVG propio renderiza la jerarquía completa de la finca con colores
fenológicos sin depender de tiles externos ni de Google Maps. Es más rápido,
funciona offline y puede embeberse en los reportes PDF generados por WeasyPrint.

### Rechazado
- Leaflet para todo: los tiles satelitales requieren conexión constante y no
  se pueden embeber en PDF.
- Google Maps: costo por llamada de API y dependencia de un servicio privado.

---

## ADR-009 — Angular 21 standalone con signals

**Estado:** Adoptado  
**Fecha:** 2026-05

### Decisión
El frontend usa Angular 21 con standalone components, signals para estado
reactivo y la nueva sintaxis @if/@for.

### Justificación
Angular impone estructura modular y tipado estricto con TypeScript, lo que
es crítico para un proyecto de esta complejidad desarrollado en solitario.
Los signals simplifican la reactividad sin NgRx. La nueva sintaxis @if/@for
mejora la legibilidad del template.

### Rechazado
- Vue 3: más flexible pero esa flexibilidad puede ser contraproducente para
  un desarrollador solo con un sistema de alta complejidad.
- React: ecosistema más fragmentado, requiere más decisiones de arquitectura
  adicionales (estado, router, forms).

---

## ADR-010 — JWT con refresh tokens y 2FA TOTP

**Estado:** Adoptado  
**Fecha:** 2026-05

### Decisión
- Access token: 15 minutos de vida
- Refresh token: 7 días, almacenado en base de datos con posibilidad de revocación
- 2FA TOTP (pyotp + qrcode): obligatorio para admin, opcional para agricultor y agrónomo

### Justificación
El sistema contiene datos productivos y financieros reales de familias agricultoras.
La seguridad por capas es no negociable. El 2FA obligatorio para admin protege
la configuración global del sistema y los parámetros del modelo predictivo.

