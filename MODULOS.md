# Módulos y prefijos de tareas — AgroCycle

Este documento define los módulos del sistema y los prefijos usados en Issues,
Pull Requests y Conventional Commits para mantener trazabilidad completa entre
el código y los casos de uso documentados en la fase de análisis y diseño.

---

## Prefijos de módulo

| Prefijo | Módulo | Descripción |
|---------|--------|-------------|
| AC-ADM | Administración | Gestión de usuarios, catálogos y parámetros globales |
| AC-PAR | Fincas y Parcelas | Registro de fincas, lotes, parcelas e historial productivo |
| AC-GEO | Geoespacial | Mapas, polígonos PostGIS, topografía automática |
| AC-TEM | Temporadas | Ciclo agrícola completo desde siembra hasta cosecha |
| AC-ACT | Actividades | Fertilizaciones, controles fitosanitarios, riego, mano de obra |
| AC-CLI | Climático | Open-Meteo, balance hídrico FAO-56, estrés hídrico Ks |
| AC-EST | Estimación | Motor predictivo, versiones del modelo, comparativo real vs estimado |
| AC-FIN | Financiero | Presupuesto, compras, ventas, rentabilidad |
| AC-AGR | Agrónomo | Observaciones, recomendaciones, evaluaciones, reportes firmados |
| AC-REP | Reportes | PDF, dashboards, exportación Excel |
| AC-AUT | Autenticación | JWT, 2FA, RBAC, rate limiting, recuperación de contraseña |
| AC-INF | Infraestructura | Docker, Nginx, CI/CD, base de datos, migraciones |
| AC-ML  | Modelo ML | Ridge Regression, Random Forest, versionado de modelos |
| AC-TEST | Tests | Tests unitarios, de integración y de cálculos agronómicos |
| AC-BUG | Bug | Corrección de errores independiente del módulo |
| AC-UI  | Interfaz | Pulido visual, UX, componentes del design system |

---

## Tipos de tarea

| Tipo | Cuándo usarlo |
|------|---------------|
| feat | Nueva funcionalidad completa |
| fix | Corrección de un bug |
| refactor | Cambio interno sin alterar comportamiento externo |
| test | Añadir o corregir tests |
| docs | Documentación únicamente |
| chore | Configuración, dependencias, infraestructura |
| perf | Mejora de rendimiento |
| style | Cambios de formato o CSS sin lógica |

---

## Formato de Conventional Commits
tipo(prefijo-número): descripción corta en español

Cuerpo opcional explicando el por qué, no el qué.
El qué ya lo dice el código.

Closes #número-de-issue

### Ejemplos reales del proyecto
feat(AC-CLI-004): implementar registro de evento climático manual con escala descriptiva

El agricultor no puede medir milímetros. La escala leve/moderada/fuerte/muy_fuerte
se convierte internamente a mm estimados para el balance hídrico.

Closes #12
fix(AC-BUG-001): corregir import get_db en climatico_routes.py

Reemplaza SessionLocal() directo por el generador get_db() para consistencia
con el patrón usado en el resto de los blueprints.

Closes #8
feat(AC-GEO-003): topografía automática vía OpenTopoData al delimitar parcela

Genera cuadrícula de puntos con ST_GeneratePoints dentro del polígono,
consulta altitudes NASA SRTM y calcula pendiente y orientación automáticamente.

Closes #5

---

## Casos de uso por módulo

### AC-ADM — Administración
- CU-ADM-001: Gestionar Usuarios
- CU-ADM-002: Autenticar Usuario
- CU-ADM-003: Gestionar Catálogos del Sistema
- CU-ADM-004: Configurar Parámetros del Modelo Predictivo
- CU-ADM-005: Consultar Métricas Globales del Sistema

### AC-PAR — Fincas y Parcelas
- CU-GFP-001: Registrar Finca
- CU-GFP-002: Gestionar Lotes
- CU-GFP-003: Registrar Parcela
- CU-GFP-004: Registrar Historial Productivo
- CU-GFP-005: Vincular Agrónomo a Finca
- CU-GFP-006: Visualizar Resumen de Fincas

### AC-GEO — Geoespacial
- CU-GEO-001: Delimitar Parcela en el Mapa
- CU-GEO-002: Visualizar Estado de Parcelas en el Mapa
- CU-GEO-003: Obtener Datos Topográficos Automáticos
- CU-GEO-004: Editar Polígono de Parcela
- CU-GEO-005: Visualizar Mapa General de la Finca
- CU-GEO-006: Delimitar Perímetro General de la Finca
- CU-GEO-007: Exportar Mapa como Imagen

### AC-TEM — Temporadas
- CU-TEM-001: Crear Temporada Agrícola
- CU-TEM-002: Configurar Variedad y Siembra
- CU-TEM-003: Consultar Seguimiento Fenológico
- CU-TEM-004: Registrar Producción Real y Cierre de Temporada
- CU-TEM-005: Consultar Historial de Temporadas
- CU-TEM-006: Consultar Panel Resumen de Temporada Activa
- CU-TEM-007: Registrar Estimación Inicial de Producción

### AC-ACT — Actividades
- CU-ACT-001: Registrar Actividad Agronómica
- CU-ACT-002: Registrar Fertilización
- CU-ACT-003: Registrar Control Fitosanitario
- CU-ACT-004: Registrar Mano de Obra
- CU-ACT-005: Consultar Línea de Tiempo de Actividades
- CU-ACT-006: Programar Alerta de Actividad Pendiente
- CU-ACT-007: Registrar Riego

### AC-CLI — Climático
- CU-CLI-001: Consultar Datos Climáticos por Parcela
- CU-CLI-002: Consultar Indicador de Humedad Estimada del Suelo
- CU-CLI-003: Registrar Evento Climático Manual
- CU-CLI-004: Consultar Alertas Climáticas
- CU-CLI-005: Consultar Indicador de Estrés Hídrico
- CU-CLI-006: Comparar Comportamiento Climático entre Temporadas
- CU-CLI-007: Consultar Historial Climático de la Temporada

### AC-EST — Estimación y Predicción
- CU-EST-001: Generar Estimación Inicial de Producción
- CU-EST-002: Recalcular Estimación Dinámicamente
- CU-EST-003: Consultar Estimación por Parcela y Temporada
- CU-EST-004: Consultar Margen de Error de la Estimación
- CU-EST-005: Consultar Evolución Histórica de Estimaciones
- CU-EST-006: Comparar Estimación vs Producción Real
- CU-EST-007: Consultar Factores de Influencia sobre la Estimación
- CU-EST-008: Consultar Indicadores de Precisión del Modelo

### AC-FIN — Financiero
- CU-FIN-001: Registrar Presupuesto Inicial
- CU-FIN-002: Registrar Compra e Insumo
- CU-FIN-003: Consultar Seguimiento de Gastos
- CU-FIN-004: Registrar Precio y Volumen de Venta
- CU-FIN-005: Consultar Rentabilidad de la Temporada
- CU-FIN-006: Consultar Costo por Quintal Producido
- CU-FIN-007: Comparar Resultados Financieros entre Temporadas
- CU-FIN-008: Recibir Alerta de Desviación Presupuestaria

### AC-AGR — Agrónomo
- CU-AGR-001: Acceder a Temporadas Vinculadas
- CU-AGR-002: Registrar Observación Técnica
- CU-AGR-003: Registrar Recomendación Agronómica
- CU-AGR-004: Elaborar Guía Técnica de Manejo
- CU-AGR-005: Registrar Evaluación de Campo
- CU-AGR-006: Generar y Firmar Reporte Técnico
- CU-AGR-007: Consultar Historial de Intervenciones Técnicas

### AC-REP — Reportes
- CU-REP-001: Generar Reporte Técnico PDF Completo
- CU-REP-002: Generar Reporte a Media Cosecha
- CU-REP-003: Generar Reporte Final de Temporada
- CU-REP-004: Consultar Dashboard General de Temporada
- CU-REP-005: Consultar Dashboard Comparativo entre Temporadas
- CU-REP-006: Exportar Datos en Excel
- CU-REP-007: Consultar Historial de Reportes Generados

---

## Backlog Sprint 8 — v1.1.0

| ID | Tipo | Descripción | Prioridad |
|----|------|-------------|-----------|
| AC-BUG-001 | fix | Corregir import get_db en climatico_routes.py | Alta |
| AC-BUG-002 | fix | Corregir import get_db en lotes_parcelas_routes.py | Alta |
| AC-TEM-008 | feat | Implementar detalle completo de temporada con estimación FAO | Alta |
| AC-UI-001 | style | Pulido visual módulo Temporadas lista y card | Media |
| AC-UI-002 | style | Dashboard agricultor clima en tiempo real sin hardcode | Media |
| AC-UI-003 | style | Vista humedad en módulo Mapa funcional | Media |
| AC-UI-004 | style | Validación punto dentro de finca en nuevo-lote | Media |
| AC-ML-001 | feat | Ridge Regression scikit-learn post temporada 2027 | Baja |
| AC-TEST-001 | test | Tests unitarios auth: login, 2FA, JWT | Baja |
| AC-TEST-002 | test | Tests cálculo FAO-33 y FAO-56 | Baja |
| AC-INF-001 | chore | GitHub Actions lint frontend Angular | Baja |
| AC-INF-002 | chore | GitHub Actions tests backend Flask | Baja |
| AC-INF-003 | chore | Deploy producción con Nginx | Baja |
