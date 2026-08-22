# Validación del Sistema — AgroCycle

Este documento registra la evidencia empírica del funcionamiento de AgroCycle
en condiciones reales de campo. Se actualiza al cierre de cada temporada
agrícola validada.

---

## Caso de estudio principal

**Agricultor:** Cesario Ramos  
**Ubicación:** Bramaderos, parroquia Guachanama, cantón Paltas, provincia de Loja, Ecuador  
**Cultivo:** Maíz (Zea mays)  
**Relación con el autor:** Padre de Cesar Daniel Ramos Merchán, autor del sistema  
**Rol en la validación:** Primer usuario real del sistema. Registra su temporada
completa en AgroCycle desde la preparación del terreno hasta la venta de la cosecha.

---

## Finca Ramos — Datos registrados en el sistema

| Campo | Valor |
|-------|-------|
| ID en base de datos | 09d913ce-7be8-49d6-afda-e2d9dc8b0fb8 |
| Superficie total | 65.09 ha |
| Municipio | Bramaderos, Guachanama, Paltas, Loja |
| Coordenadas aproximadas | LAT -4.2625, LON -79.2055 |
| Geometría | Polígono PostGIS con coordenadas GPS reales |

### Parcela Choza — validación principal

| Campo | Valor |
|-------|-------|
| ID en base de datos | 299dde6c-d5ec-4899-81bd-0da9252b0e4a |
| Superficie | 0.6754 ha |
| Altitud promedio | 827.9 msnm |
| Pendiente | 10.17% |
| Orientación | Este |
| Polígono | 84 vértices medidos con GPS en campo |
| Tipo de suelo | Franco arenoso |

### Parcela junto al río

| Campo | Valor |
|-------|-------|
| Superficie | 0.5193 ha |
| Altitud promedio | 776.1 msnm |
| Pendiente | 28.63% |

---

## Temporada de desarrollo — Maíz 2026-2027

Esta temporada se usó para desarrollo y calibración inicial del sistema.
Los datos reales registrados durante esta temporada alimentaron las primeras
pruebas del modelo predictivo.

| Campo | Valor |
|-------|-------|
| Nombre | Maíz 2026-2027 |
| Fecha de inicio | 2026-12-01 |
| Fecha de fin estimada | 2027-04-30 |
| Estado | Activa durante desarrollo |
| Estimación FAO-33 | 71.24 qq/ha (±8%) |
| Producción real registrada | 48.5 qq |
| Ingresos | $660.00 |
| Gastos | $176.00 |
| Ganancia neta | $484.00 |

---

## Validación científica — Temporada 2027

**Estado:** Planificada  
**Período:** Enero 2027 — Mayo 2027  
**Fecha de auditoría comparativa:** Mayo 2027

### Protocolo de validación

1. El agricultor usa AgroCycle desde el primer día de la temporada 2027
2. Registra todas las actividades agronómicas en el sistema en tiempo real
3. El sistema consulta Open-Meteo automáticamente para las coordenadas de cada parcela
4. El modelo predictivo genera estimaciones dinámicas durante toda la temporada
5. Al finalizar la cosecha el agricultor registra la producción real obtenida
6. El sistema calcula el comparativo estimado vs real y el porcentaje de precisión
7. Los resultados se documentan en este archivo como evidencia de la tesis

### Métricas que se evaluarán

| Métrica | Descripción | Objetivo |
|---------|-------------|---------|
| Error porcentual medio (MAPE) | Diferencia promedio entre estimación y producción real | < 20% al cierre |
| Coeficiente de determinación R² | Ajuste del modelo a los datos reales | > 0.70 |
| Error absoluto medio (MAE) | Error promedio en quintales por hectárea | < 15 qq/ha |
| Precisión del indicador de humedad | Correlación con decisiones de riego del agricultor | Cualitativa |
| Utilidad percibida | Evaluación del agricultor sobre la utilidad del sistema | Encuesta estructurada |

### Mitigación del riesgo de datos insuficientes

Dado que la zona de Bramaderos tiene una sola temporada agrícola por año,
se implementaron cuatro estrategias para enriquecer el modelo antes de la
primera validación real:

1. **Datos históricos Open-Meteo:** 20 años de datos climáticos (2005-2024)
   descargados para las coordenadas exactas de Bramaderos antes del inicio
   de la temporada 2027.

2. **Entrevistas con agricultores locales:** Levantamiento de datos históricos
   de producción de temporadas anteriores mediante entrevistas estructuradas
   con agricultores de la zona.

3. **Múltiples agricultores simultáneos:** Meta de 3 a 5 agricultores de la
   zona usando el sistema durante la temporada 2027 para multiplicar los
   puntos de datos disponibles.

4. **Parámetros FAO como base inicial:** El modelo arranca con coeficientes
   de cultivo Kc y factores de respuesta al estrés Ky publicados en la
   literatura agronómica FAO para maíz en zonas semiáridas.

---

## Resultados de validación — Por completar en Mayo 2027

Esta sección se completará al finalizar la temporada agrícola 2027.

### Parcela Choza — Resultados temporada 2027

| Métrica | Valor estimado por el modelo | Valor real registrado | Error |
|---------|-----------------------------|-----------------------|-------|
| Producción qq/ha | — | — | — |
| MAPE | — | — | — |
| R² | — | — | — |

### Análisis de factores de influencia

*Por completar.*

### Conclusiones de la validación

*Por completar.*

### Recomendaciones para v2.0.0

*Por completar tras el análisis de la primera temporada real.*

---

## Validación de datos climáticos — Realizada

Los datos climáticos históricos de Open-Meteo fueron validados contra
registros observados en la zona de Bramaderos durante el período
diciembre 2025 — abril 2026. Los datos de precipitación y temperatura
de la API coinciden con los patrones de invierno descritos por el
agricultor para ese período.

---

*Este documento forma parte de la evidencia académica del Trabajo de
Titulación "AgroCycle: Sistema Web Inteligente para la Estimación y
Monitoreo de Producción Agrícola basado en Variables Climáticas,
Territoriales y Productivas en Cultivos de Maíz de Zonas de Bosque Seco".*

*Universidad Nacional de Loja — Carrera de Computación — 2026*
