# AgroCycle 

**Sistema web inteligente para la estimación y monitoreo de producción agrícola en cultivos de maíz de zonas de bosque seco**

> Trabajo de Titulación — Ingeniería en Computación  
> Universidad Nacional de Loja, Ecuador · 2026  
> Autor: Cesar Daniel Ramos Merchán

---

## ¿Qué es AgroCycle?

AgroCycle es una plataforma web diseñada para agricultores de maíz en las zonas de bosque seco del sur del Ecuador, una región donde cientos de familias dependen de una única temporada de lluvias al año para sostener su economía. El sistema combina datos climáticos en tiempo real, información geoespacial de cada parcela y registros agronómicos para generar estimaciones dinámicas de producción antes de que finalice la cosecha.

El proyecto nace de una problemática real y personal: el autor es hijo de agricultor de maíz en Bramaderos, parroquia Guachanama, cantón Paltas, Loja. El primer usuario real del sistema es su padre, quien validará AgroCycle durante la temporada agrícola 2027.

---

## El problema que resuelve

En el bosque seco del sur del Ecuador, los agricultores toman sus decisiones más críticas mirando el cielo, sin datos, sin herramientas, basándose únicamente en experiencia generacional. Las consecuencias son directas:

- Pérdidas productivas por estrés hídrico no detectado a tiempo
- Sin estimación de rendimiento antes de la cosecha
- Sin control financiero real de la temporada
- Acceso inequitativo al agua de riego entre agricultores del mismo canal
- Precios de venta impuestos por intermediarios sin información técnica de respaldo

AgroCycle convierte esa incertidumbre en información accionable.

---

## Funcionalidades principales

| Módulo | Descripción |
|--------|-------------|
| **Mapa geoespacial** | Delimitación de fincas, lotes y parcelas con polígonos irregulares sobre imágenes satelitales. Topografía automática vía NASA SRTM |
| **Temporadas agrícolas** | Gestión del ciclo completo desde siembra hasta cosecha. Seguimiento fenológico automático |
| **Climático** | Integración con Open-Meteo API. Indicador de humedad del suelo sin sensores. Alertas de estrés hídrico |
| **Estimación y predicción** | Modelo FAO-56 + Ridge Regression con scikit-learn. Mejora progresiva con cada temporada |
| **Actividades agronómicas** | Registro de fertilizaciones, controles fitosanitarios, riego y mano de obra |
| **Finanzas** | Control de gastos, ingresos, rentabilidad y costo por quintal producido |
| **Módulo agrónomo** | Observaciones técnicas, recomendaciones y evaluaciones de campo firmadas digitalmente |
| **Reportes PDF** | Reportes técnicos completos con mapas, gráficos y firma del agrónomo |

---

## Stack tecnológico

### Backend
- **Python 3.11** + **Flask 3.1** — API REST
- **PostgreSQL 16** + **PostGIS 3.4** — Base de datos geoespacial
- **Redis 7.2** — Caché multinivel y broker de tareas
- **Celery 5.4** — Procesamiento asíncrono (consultas climáticas, recálculo del modelo, generación de PDFs)
- **SQLAlchemy 2.0** + **GeoAlchemy2** — ORM con soporte geoespacial
- **scikit-learn** + **pandas** + **numpy** — Motor predictivo de producción
- **WeasyPrint** — Generación de reportes PDF
- **JWT** + **RBAC** + **2FA (TOTP)** — Seguridad por capas

### Frontend
- **Angular 21** — Standalone components, signals, nueva sintaxis @if/@for
- **Leaflet 1.9** — Dibujo de polígonos geoespaciales sobre imágenes satelitales
- **Chart.js 4.4** — Visualización de datos climáticos y estimaciones
- **SVG propio** — Renderizado del mapa jerárquico finca → lote → parcela
- **SCSS** — Design system propio "AgroCycle Spatial Design System"

### Infraestructura
- **Docker** + **Docker Compose** — Todos los servicios containerizados
- **Nginx** — Reverse proxy con SSL (producción)

### APIs externas
- **Open-Meteo** — Datos climáticos históricos desde 1940 y tiempo real
- **OpenTopoData (NASA SRTM)** — Altitud y pendiente por coordenadas GPS

---

## Arquitectura

El sistema sigue **Clean Architecture** con cuatro capas estrictas:

```
domain/          → Entidades y contratos (sin dependencias externas)
application/     → 69 casos de uso, uno por funcionalidad
infrastructure/  → Repositorios PostgreSQL, clientes de APIs externas, ML
interfaces/      → Rutas Flask, esquemas de validación, middleware
```

**Patrones de diseño implementados:**
Repository · Unit of Work · Strategy · Observer · Factory · Decorator · Command

**Seguridad:**
JWT con refresh tokens · RBAC por rol · Rate limiting con Redis · bcrypt · 2FA TOTP · Circuit breakers · Audit logging

---

## Estructura del repositorio

```
AgroCycle/
├── backend/
│   ├── app/
│   │   ├── domain/
│   │   ├── application/use_cases/
│   │   ├── infrastructure/
│   │   └── interfaces/api/
│   ├── tests/
│   ├── migrations/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   ├── angular.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
├── CHANGELOG.md
├── ARCHITECTURE.md
├── MODULOS.md
├── VALIDACION.md
└── RELEASES.md
```

---

## Cómo correr el proyecto localmente

### Requisitos previos
- Docker 24+ y Docker Compose v2+
- Git

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/cesar050/AgroCycle.git
cd AgroCycle

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores locales

# 3. Levantar todos los servicios
docker compose up --build

# 4. Verificar que el backend responde
curl http://localhost:5000/api/v1/health

# 5. Acceder al frontend
# http://localhost:4200
```

### Puertos locales

| Servicio | Puerto |
|----------|--------|
| Frontend Angular | 4200 |
| Backend Flask | 5000 |
| PostgreSQL + PostGIS | 5434 |
| Redis | 6380 |

---

## Roles del sistema

| Rol | Descripción |
|-----|-------------|
| **Agricultor** | Usuario principal. Gestiona fincas, temporadas, actividades y finanzas |
| **Agrónomo** | Técnico vinculado por el agricultor. Registra observaciones y firma reportes |
| **Administrador** | Gestión global del sistema, catálogos y parámetros del modelo predictivo |

---

## El modelo predictivo

El motor de estimación evoluciona en tres fases:

1. **Fase 1 (sin datos propios):** Modelo FAO-33 con ecuación Penman-Monteith y datos climáticos históricos de Open-Meteo desde 1940
2. **Fase 2 (post primera temporada):** Ridge Regression con scikit-learn entrenada con datos reales de campo
3. **Fase 3 (múltiples temporadas):** Random Forest con aprendizaje incremental. El modelo mejora automáticamente al cierre de cada temporada

El sistema implementa versionado de modelos — nunca reemplaza un modelo más preciso por uno menos preciso, aunque el reentrenamiento falle en una temporada atípica.

---

## Validación real

La primera validación científica del sistema ocurrirá durante la **temporada agrícola 2027** en la **Finca Ramos, Bramaderos, Guachanama, Paltas, Loja**. Los datos reales de producción, clima y actividades de esa temporada serán la evidencia empírica del funcionamiento del modelo predictivo, documentada en [`VALIDACION.md`](./VALIDACION.md).

Una auditoría comparativa está planificada para **mayo 2027**.

---

## Estado del proyecto

| Componente | Versión | Estado |
|-----------|---------|--------|
| Backend Flask | v1.0.0 | ✅ Completo |
| Frontend Angular | v1.0.0 | ✅ Completo |
| Modelo predictivo ML | v0.1.0 | 🔄 En desarrollo |
| Tests automáticos | — | 📋 Planificado |
| Deploy producción | — | 📋 Planificado |

---

## Roadmap

**v1.1.0 — En curso**
- Corrección de bugs conocidos en rutas del backend
- Pulido visual de todos los módulos
- Tests unitarios en flujos críticos de autenticación y cálculo FAO

**v1.2.0 — Planificado**
- Implementación completa del modelo Ridge Regression
- GitHub Actions CI/CD
- Deploy en producción con Nginx

**v2.0.0 — Post temporada 2027**
- Random Forest con datos reales de la primera temporada de validación
- Modo offline con sincronización
- Expansión a otros agricultores de la zona

---

## Reconocimientos

Este proyecto fue seleccionado como postulante al **Global Innovation Challenge 2026** organizado por Social Shifters, concurso internacional para proyectos de impacto social y ambiental alineados con los ODS de las Naciones Unidas.

**ODS relacionados:** ODS 2 Hambre Cero · ODS 9 Innovación e Infraestructura · ODS 13 Acción por el Clima · ODS 1 Fin de la Pobreza

---

## Contacto

**Cesar Daniel Ramos Merchán**  
Estudiante de Ingeniería en Computación  
Universidad Nacional de Loja — Ecuador  

[![GitHub](https://img.shields.io/badge/GitHub-cesar050-181717?logo=github)](https://github.com/cesar050)

---

*AgroCycle — Decisiones informadas, cosechas más productivas.*