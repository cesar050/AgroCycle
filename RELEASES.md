# Releases — AgroCycle

Este documento registra las combinaciones de versiones desplegadas juntas
en cada release del sistema. Backend y frontend se versionan de forma
independiente pero se despliegan siempre como par compatible.

---

## Release v1.0.0 — 2026-08-22

**Estado:** Estable — desarrollo local  
**Tipo:** Release inicial — sistema completo tres roles

| Componente | Versión | Tag Git |
|-----------|---------|---------|
| Backend Flask | 1.0.0 | backend-v1.0.0 |
| Frontend Angular | 1.0.0 | frontend-v1.0.0 |
| PostgreSQL + PostGIS | 16 + 3.4 | — |
| Redis | 7.2 | — |
| Celery | 5.4 | — |

### Qué incluye este release

**Backend:**
- Auth completo: JWT, refresh tokens, RBAC, 2FA TOTP, rate limiting Redis
- Módulo geoespacial: fincas, lotes, parcelas con polígonos PostGIS
- Topografía automática vía NASA SRTM
- Temporadas agrícolas: CU-TEM-001 al CU-TEM-007
- Actividades agronómicas: fertilización, fitosanitario, riego, mano de obra
- Climático: Open-Meteo, FAO-56, balance hídrico, Ks, alertas
- Financiero: presupuesto, compras, ventas, rentabilidad
- Módulo agrónomo: observaciones, recomendaciones, evaluaciones
- Reportes PDF con WeasyPrint
- 69 casos de uso implementados en Clean Architecture

**Frontend:**
- Layout completo rol Agricultor con sidebar verde
- Layout completo rol Agrónomo con sidebar azul
- Layout completo rol Administrador con sidebar morado
- Dashboard con mapa SVG propio y gráficos Chart.js
- Módulo Mapa con Leaflet para dibujo de polígonos
- Todos los módulos funcionales excepto detalle de temporada

### Bugs conocidos en este release

| ID | Descripción | Impacto |
|----|-------------|---------|
| AC-BUG-001 | get_db no importado en climatico_routes.py | Medio |
| AC-BUG-002 | get_db no importado en lotes_parcelas_routes.py | Medio |
| AC-UI-001 | Detalle de temporada es placeholder | Alto para v1.1.0 |
| AC-UI-002 | Dashboard clima hardcodeado | Bajo |

### Cómo desplegar este release

```bash
git clone https://github.com/cesar050/AgroCycle.git
cd AgroCycle
git checkout backend-v1.0.0
cp .env.example .env
# Editar .env con valores locales
docker compose up --build
```

---

## Release v1.1.0 — Planificado

**Estado:** En desarrollo  
**Objetivo:** Estabilización y pulido visual

| Componente | Versión planificada |
|-----------|-------------------|
| Backend Flask | 1.1.0 |
| Frontend Angular | 1.1.0 |

**Incluirá:**
- Corrección AC-BUG-001 y AC-BUG-002
- Detalle de temporada completo con estimación FAO
- Dashboard clima en tiempo real
- Tests unitarios en flujos críticos
- GitHub Actions CI básico

---

## Release v1.2.0 — Planificado

**Estado:** Planificado  
**Objetivo:** CI/CD y deploy producción

| Componente | Versión planificada |
|-----------|-------------------|
| Backend Flask | 1.2.0 |
| Frontend Angular | 1.2.0 |

**Incluirá:**
- GitHub Actions completo con tests automáticos
- Deploy producción con Nginx
- Modo offline con sincronización
- SSL con Let's Encrypt

---

## Release v2.0.0 — Post temporada 2027

**Estado:** Planificado  
**Objetivo:** Modelo predictivo con datos reales de campo

| Componente | Versión planificada |
|-----------|-------------------|
| Backend Flask | 2.0.0 |
| Frontend Angular | 2.0.0 |
| Modelo ML | 1.0.0 |

**Incluirá:**
- Ridge Regression entrenada con datos reales temporada 2027
- Random Forest con aprendizaje incremental
- Versionado automático de modelos al cierre de temporada
- Resultados de validación científica documentados en VALIDACION.md
- Expansión a otros agricultores de la zona de Bramaderos
