# Changelog — AgroCycle

Todos los cambios notables de este proyecto se documentan en este archivo.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).
Versionado semántico independiente por componente: `backend-vX.Y.Z` y `frontend-vX.Y.Z`.

---

## Backend

### [backend-v1.0.0] — 2026-08-22

#### Añadido
- Autenticación completa: JWT con refresh tokens, RBAC por rol, 2FA TOTP obligatorio para admin y opcional para agricultor y agrónomo
- Recuperación y reset de contraseña vía correo Gmail (puerto 465, SSL)
- Rate limiting con Redis para endpoints de autenticación
- Módulo geoespacial: registro de fincas, lotes y parcelas con polígonos PostGIS
- Tolerancia de 10m con ST_Buffer para polígonos dibujados a mano por el agricultor
- Topografía automática vía OpenTopoData NASA SRTM por cuadrícula de puntos dentro del polígono
- Endpoints de mapa jerárquico: /fincas/:id/mapa y /fincas/:id/mapa/topografia
- Módulo de temporadas agrícolas completo (CU-TEM-001 al CU-TEM-007)
- Módulo de actividades agronómicas: fertilización, control fitosanitario, riego, mano de obra
- Contribución hídrica automática del riego al balance hídrico (perdido: 6mm/h, aspersión: 4mm/h, goteo: 2mm/h)
- Módulo climático: integración Open-Meteo histórico y forecast, FAO-56 balance hídrico, Ks estrés hídrico
- Alertas climáticas automáticas por condiciones críticas
- Registro manual de eventos climáticos no capturados por la API
- Módulo financiero: presupuesto, compras, ventas, rentabilidad por temporada
- Módulo agrónomo: observaciones técnicas, recomendaciones, evaluaciones de campo
- Generación de reportes PDF con WeasyPrint
- Índices PostgreSQL en columnas de alta frecuencia de consulta
- Índice GIST espacial en columna geometria de parcelas
- Audit logging estructurado para operaciones críticas
- Circuit breakers para servicios externos (Open-Meteo, OpenTopoData)
- Soft delete en actividades (AC-ACT-007)
- Historial de temporadas paginado (CU-TEM-006)

#### Conocido — pendiente en v1.1.0
- climatico_routes.py usa SessionLocal() directamente en lugar del generador get_db()
- lotes_parcelas_routes.py mismo patrón inconsistente
- Módulo detalle de temporada (/app/temporada/:id) es placeholder en el frontend

---

## Frontend

### [frontend-v1.0.0] — 2026-08-22

#### Añadido
- Layout completo para rol Agricultor con sidebar verde (secciones PRINCIPAL, GESTIÓN, ANÁLISIS)
- Dashboard del agricultor: mapa SVG de la finca con proyección geográfica real, gráfico Chart.js de balance Ks
- Módulo Mapa: nueva-finca, nuevo-lote, nueva-parcela con Leaflet para dibujo de polígonos
- Renderer SVG propio para visualización del mapa finca→lote→parcela coloreado por etapa fenológica
- Vista de topografía con color por pendiente
- Módulo Temporadas: lista y creación de temporadas
- Módulo Actividades: registro completo de actividades agronómicas
- Módulo Climático: visualización histórica y forecast, indicador de humedad y estrés hídrico
- Módulo Finanzas: gastos, ingresos y rentabilidad
- Módulo Reportes: generación y descarga de PDF
- Módulo Recomendaciones: lectura de recomendaciones del agrónomo
- Layout completo para rol Agrónomo con sidebar azul
- Dashboard agrónomo, fincas asignadas, observaciones, recomendaciones, evaluaciones
- Layout completo para rol Administrador con sidebar morado y badge Admin
- Dashboard admin, gestión de usuarios, fincas del sistema, configuración del sistema
- Design system AgroCycle Spatial Design System en SCSS
- Paleta fenológica SVG: pre_siembra #5E3B1E, emergencia #7FBF3F, crecimiento #4E9F3D, floracion #2E7D32, llenado_grano #E8C547, maduracion/cosecha #D4A017

#### Conocido — pendiente en v1.1.0
- Detalle de temporada (/app/temporada/:id) muestra placeholder "En construcción"
- Dashboard agricultor tiene temperatura y humedad hardcodeadas (22.8°C, 84.9%)
- Vista de humedad en módulo Mapa no está conectada al backend
- Validación Ray Casting en nuevo-lote no muestra mensaje visual completo

---

[backend-v1.0.0]: https://github.com/cesar050/AgroCycle/releases/tag/backend-v1.0.0
[frontend-v1.0.0]: https://github.com/cesar050/AgroCycle/releases/tag/frontend-v1.0.0
