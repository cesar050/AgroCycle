"""
Genera gráficos como imágenes PNG en base64 para embedar
directamente en el HTML del PDF sin archivos temporales.
Usa matplotlib con estilo profesional acorde a la identidad
visual de AgroCycle.
"""
import io
import base64
import matplotlib
matplotlib.use('Agg')  # Backend sin pantalla — obligatorio en Docker
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import numpy as np


# Paleta de colores AgroCycle
VERDE_OSCURO  = '#1B4332'
VERDE_MEDIO   = '#2D6A4F'
VERDE_CLARO   = '#52B788'
VERDE_SUAVE   = '#D8F3DC'
DORADO        = '#E9C46A'
GRIS_CLARO    = '#F7F7F7'
ROJO_ALERTA   = '#C0392B'
NARANJA       = '#E67E22'
AZUL_AGUA     = '#2980B9'


def _fig_a_base64(fig) -> str:
    """
    Convierte una figura matplotlib a string base64
    para embedar en el HTML como <img src="data:image/png;base64,...">
    """
    buffer = io.BytesIO()
    fig.savefig(
        buffer,
        format='png',
        dpi=150,
        bbox_inches='tight',
        facecolor='white',
        edgecolor='none',
    )
    buffer.seek(0)
    imagen_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close(fig)
    return f"data:image/png;base64,{imagen_base64}"


def grafico_ks_por_etapa(parametros_tecnicos: dict) -> str:
    """
    Gráfico de barras horizontales del coeficiente de estrés
    hídrico Ks por etapa fenológica.

    Color por nivel:
    - Verde oscuro: Ks >= 0.90 (óptimo)
    - Dorado:       Ks >= 0.75 (leve)
    - Naranja:      Ks >= 0.50 (moderado)
    - Rojo:         Ks <  0.50 (severo)
    """
    etapas = parametros_tecnicos.get('por_etapa', [])
    if not etapas:
        return None

    nombres = [e['etapa'] for e in etapas]
    valores = [e['ks_promedio'] for e in etapas]
    colores = []
    for v in valores:
        if v >= 0.90:
            colores.append(VERDE_MEDIO)
        elif v >= 0.75:
            colores.append(DORADO)
        elif v >= 0.50:
            colores.append(NARANJA)
        else:
            colores.append(ROJO_ALERTA)

    fig, ax = plt.subplots(figsize=(7, 3))
    fig.patch.set_facecolor('white')

    barras = ax.barh(nombres, valores, color=colores, height=0.5, zorder=3)

    # Línea de referencia Ks=1.0
    ax.axvline(x=1.0, color=VERDE_OSCURO, linewidth=1.5,
               linestyle='--', alpha=0.5, zorder=2)

    # Zona óptima sombreada
    ax.axvspan(0.90, 1.05, alpha=0.08, color=VERDE_CLARO, zorder=1)

    # Valores al final de cada barra
    for barra, valor in zip(barras, valores):
        ax.text(
            valor + 0.01,
            barra.get_y() + barra.get_height() / 2,
            f'{valor:.3f}',
            va='center', ha='left',
            fontsize=8, fontweight='bold',
            color=VERDE_OSCURO,
        )

    ax.set_xlim(0, 1.10)
    ax.set_xlabel('Coeficiente de Estrés Hídrico (Ks)', fontsize=8,
                  color=VERDE_OSCURO)
    ax.set_title('Balance Hídrico FAO-56 — Ks por Etapa Fenológica',
                 fontsize=9, fontweight='bold', color=VERDE_OSCURO, pad=8)
    ax.tick_params(axis='both', labelsize=7.5)
    ax.set_facecolor(GRIS_CLARO)
    ax.grid(axis='x', alpha=0.4, color='white', zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Leyenda
    leyenda = [
        mpatches.Patch(color=VERDE_MEDIO, label='Óptimo (≥0.90)'),
        mpatches.Patch(color=DORADO,      label='Leve (≥0.75)'),
        mpatches.Patch(color=NARANJA,     label='Moderado (≥0.50)'),
        mpatches.Patch(color=ROJO_ALERTA, label='Severo (<0.50)'),
    ]
    ax.legend(handles=leyenda, loc='lower right', fontsize=6.5,
              framealpha=0.9)

    plt.tight_layout()
    return _fig_a_base64(fig)


def grafico_humedad_diaria(datos_climaticos_diarios: list) -> str:
    """
    Gráfico de línea de la humedad del suelo día a día durante
    la temporada. Muestra la zona segura (60-80%) sombreada.

    datos_climaticos_diarios: lista de dicts con 'fecha' y
    'humedad_disponible_mm' de indicadores_estres_hidrico.
    """
    if not datos_climaticos_diarios:
        return None

    fechas = [d['fecha'] for d in datos_climaticos_diarios]
    humedad = [d['humedad_porcentaje'] for d in datos_climaticos_diarios]

    fig, ax = plt.subplots(figsize=(7, 2.8))
    fig.patch.set_facecolor('white')

    # Zona óptima sombreada
    ax.axhspan(60, 80, alpha=0.12, color=VERDE_CLARO,
               label='Zona óptima (60-80%)')

    # Líneas de referencia
    ax.axhline(y=60, color=DORADO, linewidth=0.8,
               linestyle='--', alpha=0.7)
    ax.axhline(y=80, color=VERDE_MEDIO, linewidth=0.8,
               linestyle='--', alpha=0.7)

    # Línea de humedad
    ax.plot(
        range(len(fechas)), humedad,
        color=AZUL_AGUA, linewidth=1.5,
        label='Humedad del suelo (%)',
    )
    ax.fill_between(
        range(len(fechas)), humedad, alpha=0.15, color=AZUL_AGUA
    )

    # Eje X con fechas cada 15 días
    paso = max(1, len(fechas) // 8)
    indices = range(0, len(fechas), paso)
    ax.set_xticks(list(indices))
    ax.set_xticklabels(
        [fechas[i] for i in indices],
        rotation=30, ha='right', fontsize=6.5
    )

    ax.set_ylim(0, 110)
    ax.set_ylabel('Humedad (%)', fontsize=8, color=VERDE_OSCURO)
    ax.set_title('Evolución de la Humedad del Suelo — Temporada Completa',
                 fontsize=9, fontweight='bold', color=VERDE_OSCURO, pad=8)
    ax.tick_params(axis='y', labelsize=7.5)
    ax.set_facecolor(GRIS_CLARO)
    ax.grid(alpha=0.3, color='white')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend(fontsize=7, loc='upper right', framealpha=0.9)

    plt.tight_layout()
    return _fig_a_base64(fig)


def grafico_gastos_pie(gastos: dict) -> str:
    """
    Gráfico de torta con la distribución de gastos por categoría.
    Solo muestra categorías con gasto mayor a 0.
    """
    categorias_raw = {
        'Semillas':       gastos.get('semillas', 0),
        'Fertilizantes':  gastos.get('fertilizantes', 0),
        'Agroquímicos':   gastos.get('agroquimicos', 0),
        'Mano de Obra':   gastos.get('mano_obra', 0),
        'Otros':          gastos.get('otros', 0),
    }

    # Filtrar categorías con valor > 0
    categorias = {k: v for k, v in categorias_raw.items() if v > 0}

    if not categorias or sum(categorias.values()) == 0:
        return None

    colores_pie = [
        VERDE_OSCURO, VERDE_MEDIO, VERDE_CLARO,
        DORADO, NARANJA,
    ][:len(categorias)]

    fig, ax = plt.subplots(figsize=(5, 3.5))
    fig.patch.set_facecolor('white')

    wedges, texts, autotexts = ax.pie(
        categorias.values(),
        labels=None,
        colors=colores_pie,
        autopct='%1.1f%%',
        startangle=90,
        pctdistance=0.75,
        wedgeprops={'linewidth': 2, 'edgecolor': 'white'},
    )

    for autotext in autotexts:
        autotext.set_fontsize(8)
        autotext.set_fontweight('bold')
        autotext.set_color('white')

    # Leyenda con valores en USD
    leyenda_labels = [
        f"{k}: ${v:.2f}" for k, v in categorias.items()
    ]
    ax.legend(
        wedges, leyenda_labels,
        loc='center left',
        bbox_to_anchor=(1.0, 0.5),
        fontsize=7.5,
        framealpha=0.9,
    )

    total = sum(categorias.values())
    ax.text(
        0, 0, f'${total:.2f}',
        ha='center', va='center',
        fontsize=10, fontweight='bold',
        color=VERDE_OSCURO,
    )

    ax.set_title('Distribución de Gastos por Categoría',
                 fontsize=9, fontweight='bold',
                 color=VERDE_OSCURO, pad=10)

    plt.tight_layout()
    return _fig_a_base64(fig)


def grafico_precipitacion_mensual(datos_mensuales: list) -> str:
    """
    Gráfico de barras de precipitación mensual durante la temporada.
    Muestra la lluvia real de Bramaderos mes a mes.

    datos_mensuales: lista de dicts con 'mes' y 'precipitacion_mm'.
    """
    if not datos_mensuales:
        return None

    meses = [d['mes'] for d in datos_mensuales]
    precipitacion = [d['precipitacion_mm'] for d in datos_mensuales]

    # Color por nivel de precipitación
    colores = []
    for p in precipitacion:
        if p >= 100:
            colores.append(AZUL_AGUA)
        elif p >= 50:
            colores.append(VERDE_CLARO)
        else:
            colores.append(DORADO)

    fig, ax = plt.subplots(figsize=(7, 3))
    fig.patch.set_facecolor('white')

    barras = ax.bar(meses, precipitacion, color=colores,
                    width=0.6, zorder=3, edgecolor='white', linewidth=1.5)

    # Valor encima de cada barra
    for barra, valor in zip(barras, precipitacion):
        ax.text(
            barra.get_x() + barra.get_width() / 2,
            barra.get_height() + 2,
            f'{valor:.0f}',
            ha='center', va='bottom',
            fontsize=7.5, fontweight='bold',
            color=VERDE_OSCURO,
        )

    ax.set_ylabel('Precipitación (mm)', fontsize=8, color=VERDE_OSCURO)
    ax.set_title('Precipitación Mensual — Datos Reales Open-Meteo Bramaderos',
                 fontsize=9, fontweight='bold', color=VERDE_OSCURO, pad=8)
    ax.tick_params(axis='both', labelsize=7.5)
    ax.set_facecolor(GRIS_CLARO)
    ax.grid(axis='y', alpha=0.4, color='white', zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    leyenda = [
        mpatches.Patch(color=AZUL_AGUA,   label='Alta (≥100mm)'),
        mpatches.Patch(color=VERDE_CLARO, label='Media (≥50mm)'),
        mpatches.Patch(color=DORADO,      label='Baja (<50mm)'),
    ]
    ax.legend(handles=leyenda, fontsize=6.5, framealpha=0.9)

    plt.tight_layout()
    return _fig_a_base64(fig)


def grafico_progreso_ciclo(desarrollo_cultivo: dict) -> str:
    """
    Gráfico visual del progreso del ciclo vegetativo.
    Muestra cada etapa como segmento proporcional con
    la etapa actual resaltada.
    """
    etapas_config = [
        ('Emergencia',       0.05, VERDE_SUAVE),
        ('Crec. Vegetativo', 0.25, '#74C69D'),
        ('Floración',        0.25, VERDE_MEDIO),
        ('Llenado Grano',    0.25, VERDE_OSCURO),
        ('Maduración',       0.15, DORADO),
        ('Cosecha',          0.05, NARANJA),
    ]

    etapa_actual = (
        desarrollo_cultivo.get('etapa_actual', '')
        .lower()
        .replace(' ', '_')
    )
    avance = desarrollo_cultivo.get('avance_porcentaje', 0) / 100

    fig, ax = plt.subplots(figsize=(7, 1.8))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    x_inicio = 0
    for nombre, proporcion, color in etapas_config:
        nombre_norm = nombre.lower().replace(' ', '_').replace('.', '')
        es_activa = nombre_norm in etapa_actual or etapa_actual in nombre_norm

        # Barra de la etapa
        ax.barh(
            0, proporcion, left=x_inicio, height=0.5,
            color=color,
            edgecolor='white', linewidth=2,
            zorder=2,
        )

        # Resaltar etapa activa
        if es_activa:
            ax.barh(
                0, proporcion, left=x_inicio, height=0.5,
                color='none',
                edgecolor=DORADO, linewidth=3,
                zorder=3,
            )
            ax.text(
                x_inicio + proporcion / 2, 0.35,
                'ACTUAL',
                ha='center', va='bottom',
                fontsize=6, fontweight='bold',
                color=DORADO, zorder=4,
            )

        # Nombre de la etapa
        ax.text(
            x_inicio + proporcion / 2, 0,
            nombre,
            ha='center', va='center',
            fontsize=6.5, fontweight='600',
            color='white' if color in [VERDE_MEDIO, VERDE_OSCURO] else VERDE_OSCURO,
            zorder=4,
        )

        x_inicio += proporcion

    # Línea de progreso actual
    ax.axvline(x=avance, color=DORADO, linewidth=2.5,
               linestyle='-', zorder=5, alpha=0.9)
    ax.text(
        avance, -0.32,
        f'{desarrollo_cultivo.get("avance_porcentaje", 0):.1f}%',
        ha='center', va='top',
        fontsize=7.5, fontweight='bold',
        color=DORADO,
    )

    ax.set_xlim(0, 1)
    ax.set_ylim(-0.5, 0.7)
    ax.axis('off')
    ax.set_title(
        f'Progreso del Ciclo Vegetativo — '
        f'{desarrollo_cultivo.get("dias_desde_siembra", 0)} DDS '
        f'de {desarrollo_cultivo.get("ciclo_total_dias", 120)} días',
        fontsize=9, fontweight='bold',
        color=VERDE_OSCURO, pad=6,
    )

    plt.tight_layout()
    return _fig_a_base64(fig)