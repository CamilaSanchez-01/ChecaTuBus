"""
Generador de Gráficas - Checa tu Bus
Conecta con Google Sheets, lee los datos y genera gráficas profesionales.
"""

import os
import sys
import json
import logging
from collections import Counter
from datetime import datetime

# Fix encoding para Windows (soporte de emojis en terminal)
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import gspread
from google.oauth2.service_account import Credentials
import matplotlib
matplotlib.use('Agg')  # Backend sin GUI
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

# Directorio del script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GRAFICAS_DIR = os.path.join(BASE_DIR, "graficas")

# Paleta de colores vibrante y profesional
COLORES = {
    "primario": "#6366F1",      # Indigo
    "secundario": "#8B5CF6",    # Violeta
    "acento1": "#EC4899",       # Rosa
    "acento2": "#F59E0B",       # Ámbar
    "acento3": "#10B981",       # Esmeralda
    "acento4": "#3B82F6",       # Azul
    "acento5": "#EF4444",       # Rojo
    "acento6": "#14B8A6",       # Teal
    "fondo": "#0F172A",         # Slate oscuro
    "texto": "#F8FAFC",         # Blanco suave
    "grid": "#334155",          # Slate grid
    "tarjeta": "#1E293B",       # Slate medio
}

PALETA_BARRAS = ["#6366F1", "#8B5CF6", "#EC4899", "#F59E0B", "#10B981",
                 "#3B82F6", "#EF4444", "#14B8A6", "#A855F7", "#F97316",
                 "#22D3EE", "#84CC16", "#E879F9", "#FB923C", "#34D399"]

PALETA_PASTEL = ["#6366F1", "#EC4899", "#F59E0B", "#10B981", "#3B82F6",
                 "#EF4444", "#14B8A6", "#A855F7"]


def configurar_estilo():
    """Configura el estilo global de matplotlib con tema oscuro premium."""
    plt.rcParams.update({
        'figure.facecolor': COLORES["fondo"],
        'axes.facecolor': COLORES["tarjeta"],
        'axes.edgecolor': COLORES["grid"],
        'axes.labelcolor': COLORES["texto"],
        'text.color': COLORES["texto"],
        'xtick.color': COLORES["texto"],
        'ytick.color': COLORES["texto"],
        'grid.color': COLORES["grid"],
        'grid.alpha': 0.3,
        'font.size': 11,
        'axes.titlesize': 16,
        'axes.titleweight': 'bold',
        'figure.titlesize': 18,
        'legend.facecolor': COLORES["tarjeta"],
        'legend.edgecolor': COLORES["grid"],
        'legend.fontsize': 10,
    })


# ============================================================================
# CONEXIÓN A GOOGLE SHEETS
# ============================================================================

def conectar_sheets():
    """Conecta a Google Sheets y retorna el spreadsheet."""
    config_path = os.path.join(BASE_DIR, "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    creds_file = os.path.join(BASE_DIR, config["google_sheets"]["credentials_file"])
    spreadsheet_id = config["google_sheets"]["spreadsheet_id"]

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly"
    ]
    creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(spreadsheet_id)

    logger.info("✅ Conexión exitosa con Google Sheets")
    return spreadsheet


def leer_hoja(spreadsheet, nombre_hoja):
    """Lee una hoja y retorna un DataFrame de pandas."""
    try:
        ws = spreadsheet.worksheet(nombre_hoja)
        datos = ws.get_all_values()
        if len(datos) < 2:
            logger.warning(f"⚠ Hoja '{nombre_hoja}' vacía o solo encabezados")
            return pd.DataFrame()
        df = pd.DataFrame(datos[1:], columns=datos[0])
        logger.info(f"📊 '{nombre_hoja}': {len(df)} registros leídos")
        return df
    except Exception as e:
        logger.error(f"❌ Error al leer '{nombre_hoja}': {e}")
        return pd.DataFrame()


# ============================================================================
# FUNCIONES DE GRÁFICAS
# ============================================================================

def grafica_barras(datos, titulo, xlabel, ylabel, archivo, horizontal=False, top_n=None):
    """Genera una gráfica de barras profesional."""
    if datos.empty:
        logger.warning(f"⚠ Sin datos para '{titulo}'")
        return

    if top_n:
        datos = datos.head(top_n)

    fig, ax = plt.subplots(figsize=(12, 7))
    colores = PALETA_BARRAS[:len(datos)]

    if horizontal:
        bars = ax.barh(range(len(datos)), datos.values, color=colores, edgecolor='none',
                       height=0.7, zorder=3)
        ax.set_yticks(range(len(datos)))
        ax.set_yticklabels(datos.index, fontsize=10)
        ax.invert_yaxis()
        ax.set_xlabel(ylabel, fontsize=12, labelpad=10)
        ax.set_ylabel(xlabel, fontsize=12, labelpad=10)
        # Etiquetas de valor
        for bar in bars:
            width = bar.get_width()
            ax.text(width + max(datos.values) * 0.02, bar.get_y() + bar.get_height() / 2,
                    f'{int(width):,}', ha='left', va='center', fontsize=10,
                    color=COLORES["texto"], fontweight='bold')
    else:
        bars = ax.bar(range(len(datos)), datos.values, color=colores, edgecolor='none',
                      width=0.7, zorder=3)
        ax.set_xticks(range(len(datos)))
        ax.set_xticklabels(datos.index, rotation=45, ha='right', fontsize=10)
        ax.set_xlabel(xlabel, fontsize=12, labelpad=10)
        ax.set_ylabel(ylabel, fontsize=12, labelpad=10)
        # Etiquetas de valor
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height + max(datos.values) * 0.02,
                    f'{int(height):,}', ha='center', va='bottom', fontsize=10,
                    color=COLORES["texto"], fontweight='bold')

    ax.set_title(titulo, fontsize=16, fontweight='bold', pad=20, color=COLORES["texto"])
    ax.grid(axis='x' if horizontal else 'y', alpha=0.2, linestyle='--', zorder=0)
    ax.set_axisbelow(True)

    # Remover bordes superior y derecho
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(COLORES["grid"])
    ax.spines['bottom'].set_color(COLORES["grid"])

    plt.tight_layout()
    ruta = os.path.join(GRAFICAS_DIR, archivo)
    plt.savefig(ruta, dpi=150, bbox_inches='tight', facecolor=COLORES["fondo"])
    plt.close()
    logger.info(f"💾 Guardada: {archivo}")


def grafica_pastel(datos, titulo, archivo):
    """Genera una gráfica de pastel moderna."""
    if datos.empty:
        logger.warning(f"⚠ Sin datos para '{titulo}'")
        return

    fig, ax = plt.subplots(figsize=(10, 8))
    colores = PALETA_PASTEL[:len(datos)]

    wedges, texts, autotexts = ax.pie(
        datos.values,
        labels=None,
        autopct='%1.1f%%',
        colors=colores,
        pctdistance=0.75,
        startangle=140,
        wedgeprops={'edgecolor': COLORES["fondo"], 'linewidth': 2}
    )

    for autotext in autotexts:
        autotext.set_fontsize(11)
        autotext.set_fontweight('bold')
        autotext.set_color('white')

    # Donut style: agregar círculo blanco al centro
    centre_circle = plt.Circle((0, 0), 0.55, fc=COLORES["fondo"])
    ax.add_patch(centre_circle)

    # Texto central con total
    total = datos.sum()
    ax.text(0, 0.05, f'{int(total):,}', ha='center', va='center',
            fontsize=28, fontweight='bold', color=COLORES["texto"])
    ax.text(0, -0.12, 'Total', ha='center', va='center',
            fontsize=12, color='#94A3B8')

    # Leyenda
    leyenda = ax.legend(
        wedges,
        [f"{label} ({int(val):,})" for label, val in zip(datos.index, datos.values)],
        title="Categorías",
        loc="center left",
        bbox_to_anchor=(0.95, 0.5),
        fontsize=10,
        title_fontsize=12,
        framealpha=0.8
    )
    leyenda.get_title().set_color(COLORES["texto"])

    ax.set_title(titulo, fontsize=16, fontweight='bold', pad=20, color=COLORES["texto"])

    plt.tight_layout()
    ruta = os.path.join(GRAFICAS_DIR, archivo)
    plt.savefig(ruta, dpi=150, bbox_inches='tight', facecolor=COLORES["fondo"])
    plt.close()
    logger.info(f"💾 Guardada: {archivo}")


def grafica_lineas(df_series, titulo, xlabel, ylabel, archivo):
    """Genera una gráfica de líneas con gradiente."""
    if df_series.empty:
        logger.warning(f"⚠ Sin datos para '{titulo}'")
        return

    fig, ax = plt.subplots(figsize=(14, 7))

    x = range(len(df_series))
    y = df_series.values

    # Línea principal
    ax.plot(x, y, color=COLORES["primario"], linewidth=2.5, zorder=5, marker='o',
            markersize=5, markerfacecolor=COLORES["acento1"], markeredgecolor='none')

    # Área bajo la curva con gradiente
    ax.fill_between(x, y, alpha=0.15, color=COLORES["primario"], zorder=2)

    ax.set_xticks(x)
    ax.set_xticklabels(df_series.index, rotation=45, ha='right', fontsize=9)
    ax.set_xlabel(xlabel, fontsize=12, labelpad=10)
    ax.set_ylabel(ylabel, fontsize=12, labelpad=10)
    ax.set_title(titulo, fontsize=16, fontweight='bold', pad=20, color=COLORES["texto"])

    ax.grid(axis='y', alpha=0.2, linestyle='--', zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(COLORES["grid"])
    ax.spines['bottom'].set_color(COLORES["grid"])

    # Añadir media como línea punteada
    media = y.mean()
    ax.axhline(y=media, color=COLORES["acento2"], linestyle='--', linewidth=1.5,
               alpha=0.7, label=f'Promedio: {media:.0f}')
    ax.legend(loc='upper right', fontsize=10)

    plt.tight_layout()
    ruta = os.path.join(GRAFICAS_DIR, archivo)
    plt.savefig(ruta, dpi=150, bbox_inches='tight', facecolor=COLORES["fondo"])
    plt.close()
    logger.info(f"💾 Guardada: {archivo}")


# ============================================================================
# GENERACIÓN DE TODAS LAS GRÁFICAS
# ============================================================================

def generar_todas_las_graficas(spreadsheet):
    """Lee datos de las 5 hojas y genera las 10 gráficas."""

    # --- Leer datos ---
    logger.info("📥 Leyendo datos de Google Sheets...")
    df_rutas = leer_hoja(spreadsheet, "RUTAS")
    df_paradas = leer_hoja(spreadsheet, "PARADAS")
    df_unidades = leer_hoja(spreadsheet, "UNIDADES")
    df_pois = leer_hoja(spreadsheet, "PUNTOS_DE_INTERES")
    df_incidencias = leer_hoja(spreadsheet, "INCIDENCIAS_HISTORICAS")

    graficas_generadas = []

    # =====================================================================
    # 1. Rutas por Concesionario (barras)
    # =====================================================================
    if not df_rutas.empty and "Concesionario" in df_rutas.columns:
        conteo = df_rutas["Concesionario"].value_counts()
        grafica_barras(conteo, "Rutas por Concesionario",
                       "Concesionario", "Numero de Rutas",
                       "01_rutas_por_concesionario.png")
        graficas_generadas.append("01_rutas_por_concesionario.png")

    # =====================================================================
    # 2. Rutas por Tipo de Servicio (pastel)
    # =====================================================================
    if not df_rutas.empty and "Tipo_Servicio" in df_rutas.columns:
        conteo = df_rutas["Tipo_Servicio"].value_counts()
        grafica_pastel(conteo, "Distribucion por Tipo de Servicio",
                       "02_rutas_por_tipo_servicio.png")
        graficas_generadas.append("02_rutas_por_tipo_servicio.png")

    # =====================================================================
    # 3. Paradas por Tipo (barras)
    # =====================================================================
    if not df_paradas.empty and "Tipo_Parada" in df_paradas.columns:
        conteo = df_paradas["Tipo_Parada"].value_counts()
        grafica_barras(conteo, "Paradas por Tipo",
                       "Tipo de Parada", "Cantidad",
                       "03_paradas_por_tipo.png")
        graficas_generadas.append("03_paradas_por_tipo.png")

    # =====================================================================
    # 4. Top 15 Colonias con más Paradas (barras horizontales)
    # =====================================================================
    if not df_paradas.empty and "Colonia" in df_paradas.columns:
        conteo = df_paradas["Colonia"].value_counts().head(15)
        grafica_barras(conteo, "Top 15 Colonias con Mas Paradas",
                       "Colonia", "Numero de Paradas",
                       "04_top_colonias_paradas.png", horizontal=True)
        graficas_generadas.append("04_top_colonias_paradas.png")

    # =====================================================================
    # 5. Disponibilidad de GPS en Unidades (pastel)
    # =====================================================================
    if not df_unidades.empty and "GPS" in df_unidades.columns:
        conteo = df_unidades["GPS"].value_counts()
        grafica_pastel(conteo, "Disponibilidad de GPS en Unidades",
                       "05_gps_unidades.png")
        graficas_generadas.append("05_gps_unidades.png")

    # =====================================================================
    # 6. Top 10 Modelos de Unidad (barras)
    # =====================================================================
    if not df_unidades.empty and "Modelo" in df_unidades.columns:
        conteo = df_unidades["Modelo"].value_counts().head(10)
        grafica_barras(conteo, "Top 10 Modelos de Unidad",
                       "Modelo", "Cantidad",
                       "06_top_modelos_unidad.png")
        graficas_generadas.append("06_top_modelos_unidad.png")

    # =====================================================================
    # 7. Puntos de Interés por Tipo (barras)
    # =====================================================================
    if not df_pois.empty and "Tipo" in df_pois.columns:
        conteo = df_pois["Tipo"].value_counts()
        grafica_barras(conteo, "Puntos de Interes por Tipo",
                       "Tipo", "Cantidad",
                       "07_pois_por_tipo.png")
        graficas_generadas.append("07_pois_por_tipo.png")

    # =====================================================================
    # 8. Incidencias por Tipo (barras)
    # =====================================================================
    if not df_incidencias.empty and "Tipo_Incidencia" in df_incidencias.columns:
        conteo = df_incidencias["Tipo_Incidencia"].value_counts()
        grafica_barras(conteo, "Incidencias por Tipo",
                       "Tipo de Incidencia", "Cantidad",
                       "08_incidencias_por_tipo.png")
        graficas_generadas.append("08_incidencias_por_tipo.png")

    # =====================================================================
    # 9. Incidencias por Mes (líneas temporal)
    # =====================================================================
    if not df_incidencias.empty and "Fecha" in df_incidencias.columns:
        try:
            df_inc_temp = df_incidencias.copy()
            df_inc_temp["Fecha_dt"] = pd.to_datetime(df_inc_temp["Fecha"], errors='coerce')
            df_inc_temp = df_inc_temp.dropna(subset=["Fecha_dt"])
            df_inc_temp["AnoMes"] = df_inc_temp["Fecha_dt"].dt.to_period("M")
            conteo_mensual = df_inc_temp.groupby("AnoMes").size()
            conteo_mensual.index = conteo_mensual.index.astype(str)
            if len(conteo_mensual) > 0:
                grafica_lineas(conteo_mensual, "Incidencias por Mes (Tendencia Temporal)",
                               "Mes", "Numero de Incidencias",
                               "09_incidencias_por_mes.png")
                graficas_generadas.append("09_incidencias_por_mes.png")
        except Exception as e:
            logger.warning(f"⚠ Error al procesar fechas de incidencias: {e}")

    # =====================================================================
    # 10. Top 10 Rutas con más Incidencias (barras horizontales)
    # =====================================================================
    if not df_incidencias.empty and "Ruta_Afectada" in df_incidencias.columns:
        conteo = df_incidencias["Ruta_Afectada"].value_counts().head(10)
        # Intentar mapear nombres de ruta
        if not df_rutas.empty and "ID_Ruta" in df_rutas.columns and "Nombre_Ruta" in df_rutas.columns:
            mapa_rutas = dict(zip(df_rutas["ID_Ruta"], df_rutas["Nombre_Ruta"]))
            conteo.index = [mapa_rutas.get(idx, idx) for idx in conteo.index]
            # Truncar nombres largos
            conteo.index = [n[:35] + "..." if len(n) > 35 else n for n in conteo.index]
        grafica_barras(conteo, "Top 10 Rutas con Mas Incidencias",
                       "Ruta", "Numero de Incidencias",
                       "10_top_rutas_incidencias.png", horizontal=True)
        graficas_generadas.append("10_top_rutas_incidencias.png")

    return graficas_generadas


# ============================================================================
# GENERACIÓN DEL DASHBOARD HTML
# ============================================================================

def generar_dashboard_html(graficas, resumen):
    """Genera un dashboard HTML que muestra todas las gráficas."""

    tarjetas_resumen = ""
    iconos = {"RUTAS": "🚌", "PARADAS": "🚏", "UNIDADES": "🚐",
              "PUNTOS_DE_INTERES": "📍", "INCIDENCIAS_HISTORICAS": "⚠️"}
    nombres_bonitos = {"RUTAS": "Rutas", "PARADAS": "Paradas", "UNIDADES": "Unidades",
                       "PUNTOS_DE_INTERES": "Puntos de Interés",
                       "INCIDENCIAS_HISTORICAS": "Incidencias"}

    for hoja, count in resumen.items():
        if hoja == "TOTAL":
            continue
        icono = iconos.get(hoja, "📊")
        nombre = nombres_bonitos.get(hoja, hoja)
        tarjetas_resumen += f"""
            <div class="stat-card">
                <div class="stat-icon">{icono}</div>
                <div class="stat-value">{count:,}</div>
                <div class="stat-label">{nombre}</div>
            </div>"""

    imagenes_html = ""
    for g in graficas:
        titulo = g.replace(".png", "").replace("_", " ").lstrip("0123456789_")
        imagenes_html += f"""
            <div class="chart-card">
                <img src="{g}" alt="{titulo}" loading="lazy">
            </div>"""

    total = resumen.get("TOTAL", 0)
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Checa tu Bus - Dashboard de Datos</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #0F172A;
            color: #F8FAFC;
            min-height: 100vh;
        }}

        .header {{
            background: linear-gradient(135deg, #1E1B4B 0%, #312E81 50%, #4338CA 100%);
            padding: 2.5rem 2rem;
            text-align: center;
            border-bottom: 1px solid rgba(99, 102, 241, 0.3);
            position: relative;
            overflow: hidden;
        }}

        .header::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle at 30% 50%, rgba(99, 102, 241, 0.1) 0%, transparent 50%),
                        radial-gradient(circle at 70% 50%, rgba(236, 72, 153, 0.08) 0%, transparent 50%);
            pointer-events: none;
        }}

        .header h1 {{
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #C7D2FE, #F8FAFC, #DDD6FE);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
            position: relative;
        }}

        .header .subtitle {{
            color: #A5B4FC;
            font-size: 1.1rem;
            font-weight: 400;
            position: relative;
        }}

        .header .date {{
            color: #818CF8;
            font-size: 0.85rem;
            margin-top: 0.5rem;
            position: relative;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
            padding: 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }}

        .stat-card {{
            background: linear-gradient(145deg, #1E293B, #1A2332);
            border: 1px solid #334155;
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}

        .stat-card::after {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #6366F1, #EC4899);
            opacity: 0;
            transition: opacity 0.3s ease;
        }}

        .stat-card:hover {{
            transform: translateY(-4px);
            border-color: #6366F1;
            box-shadow: 0 8px 25px rgba(99, 102, 241, 0.15);
        }}

        .stat-card:hover::after {{
            opacity: 1;
        }}

        .stat-icon {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}

        .stat-value {{
            font-size: 2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #6366F1, #8B5CF6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .stat-label {{
            color: #94A3B8;
            font-size: 0.85rem;
            font-weight: 500;
            margin-top: 0.25rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .total-bar {{
            max-width: 1400px;
            margin: 0 auto 1rem;
            padding: 0 2rem;
        }}

        .total-bar-inner {{
            background: linear-gradient(135deg, #312E81, #4338CA);
            border-radius: 12px;
            padding: 1rem 2rem;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 1rem;
            border: 1px solid rgba(99, 102, 241, 0.3);
        }}

        .total-bar-inner span {{
            font-size: 1.1rem;
            font-weight: 600;
        }}

        .total-bar-inner .total-num {{
            font-size: 1.4rem;
            font-weight: 800;
            color: #C7D2FE;
        }}

        .charts-section {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 1rem 2rem 3rem;
        }}

        .charts-section h2 {{
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
            color: #E2E8F0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(550px, 1fr));
            gap: 1.5rem;
        }}

        .chart-card {{
            background: linear-gradient(145deg, #1E293B, #1A2332);
            border: 1px solid #334155;
            border-radius: 16px;
            padding: 1rem;
            transition: all 0.3s ease;
            overflow: hidden;
        }}

        .chart-card:hover {{
            border-color: #6366F1;
            box-shadow: 0 8px 25px rgba(99, 102, 241, 0.1);
        }}

        .chart-card img {{
            width: 100%;
            height: auto;
            border-radius: 10px;
            display: block;
        }}

        .footer {{
            text-align: center;
            padding: 2rem;
            color: #475569;
            font-size: 0.85rem;
            border-top: 1px solid #1E293B;
        }}

        .footer a {{
            color: #6366F1;
            text-decoration: none;
        }}

        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.8rem;
            }}
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
                padding: 1rem;
            }}
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
            .charts-section {{
                padding: 1rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚌 Checa tu Bus</h1>
        <div class="subtitle">Dashboard de Análisis de Datos — Transporte Público de Tijuana</div>
        <div class="date">Generado: {fecha}</div>
    </div>

    <div class="stats-grid">
        {tarjetas_resumen}
    </div>

    <div class="total-bar">
        <div class="total-bar-inner">
            <span>📊 Total de registros en la base de datos:</span>
            <span class="total-num">{total:,}</span>
        </div>
    </div>

    <div class="charts-section">
        <h2>📈 Visualización de Datos</h2>
        <div class="charts-grid">
            {imagenes_html}
        </div>
    </div>

    <div class="footer">
        <p>Checa tu Bus &copy; 2026 — Datos extraídos de <a href="https://docs.google.com/spreadsheets/d/1Ykv1whSLXsvuxrVfNrtAnEXpF_X7gc_s2gCDzirGoXY">Google Sheets</a></p>
    </div>
</body>
</html>"""

    ruta_html = os.path.join(GRAFICAS_DIR, "dashboard.html")
    with open(ruta_html, "w", encoding="utf-8") as f:
        f.write(html)
    logger.info(f"🌐 Dashboard guardado: {ruta_html}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Función principal: conecta, lee, genera gráficas y dashboard."""
    print("\n" + "=" * 60)
    print("   🚌 CHECA TU BUS - Generador de Gráficas")
    print("=" * 60 + "\n")

    # Crear carpeta de gráficas
    os.makedirs(GRAFICAS_DIR, exist_ok=True)

    # Configurar estilo
    configurar_estilo()

    # Conectar
    spreadsheet = conectar_sheets()

    # Generar gráficas
    graficas = generar_todas_las_graficas(spreadsheet)

    # Obtener resumen para el dashboard
    from sheets_manager import ENCABEZADOS
    resumen = {}
    total = 0
    for nombre_hoja in ENCABEZADOS:
        try:
            ws = spreadsheet.worksheet(nombre_hoja)
            count = max(0, len(ws.get_all_values()) - 1)
            resumen[nombre_hoja] = count
            total += count
        except Exception:
            resumen[nombre_hoja] = 0
    resumen["TOTAL"] = total

    # Generar dashboard HTML
    generar_dashboard_html(graficas, resumen)

    # Resumen final
    print("\n" + "=" * 60)
    print(f"   ✅ {len(graficas)} gráficas generadas exitosamente")
    print(f"   📁 Carpeta: {GRAFICAS_DIR}")
    print(f"   🌐 Dashboard: graficas/dashboard.html")
    print(f"   📊 Total registros: {total:,}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
