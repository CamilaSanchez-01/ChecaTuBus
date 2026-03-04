#!/usr/bin/env python3
"""
=============================================================================
SCRAPER DE TRANSPORTE PÚBLICO - TIJUANA, B.C.
=============================================================================
Proyecto universitario: Sistema de información de rutas de transporte público.
Recopila datos sobre rutas, paradas, unidades, puntos de interés e incidencias
y los sube a Google Sheets.

Uso:
    python scraper_transporte_tijuana.py           # Ejecución completa
    python scraper_transporte_tijuana.py --test     # Solo verificar conexión
    python scraper_transporte_tijuana.py --fase 1   # Ejecutar solo fase 1

Autor: Proyecto Checa tu Bus
Fecha: 2026-02-24
=============================================================================
"""

import json
import sys
import os
import logging
import argparse
from datetime import datetime

# Configurar el directorio de trabajo al mismo del script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ============================================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================================
import io

# Crear un stream con encoding UTF-8 para que los emojis no causen error en Windows
_stdout_utf8 = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("log.txt", encoding="utf-8"),
        logging.StreamHandler(_stdout_utf8)
    ]
)
logger = logging.getLogger(__name__)

# Importar módulos del proyecto
from sheets_manager import GoogleSheetsManager
from web_scraper import WebScraper
from generadores import (
    generar_rutas,
    generar_paradas,
    generar_unidades,
    generar_puntos_interes,
    generar_incidencias
)


def cargar_configuracion():
    """Carga la configuración desde config.json."""
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        logger.info("✅ Configuración cargada correctamente")
        return config
    except FileNotFoundError:
        logger.error("❌ No se encontró config.json")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"❌ Error al parsear config.json: {e}")
        sys.exit(1)


def modo_test(config):
    """
    Modo de prueba: verifica conexión con Google Sheets,
    crea hojas y escribe 2 registros de prueba en cada una.
    """
    logger.info("=" * 60)
    logger.info("🧪 MODO TEST - Verificando conexión y estructura")
    logger.info("=" * 60)

    gs_config = config["google_sheets"]
    manager = GoogleSheetsManager(
        gs_config["credentials_file"],
        gs_config["spreadsheet_id"]
    )

    # Verificar/crear hojas
    manager.verificar_o_crear_hojas()

    # Escribir 2 registros de prueba en cada hoja
    from generadores import FECHA_HOY
    pruebas = {
        "RUTAS": [
            ["RUT-TEST1", "Ruta Test 1", "ATT", "Normal", "Centro, Test",
             "Av. Test", "Test", FECHA_HOY],
            ["RUT-TEST2", "Ruta Test 2", "ALTISA", "Express", "Zona Río, Test",
             "Blvd. Test", "Test", FECHA_HOY],
        ],
        "PARADAS": [
            ["PAR-TEST1", "Parada Test 1", "RUT-TEST1", 32.5290, -117.0240,
             "Centro", "Av. Test", "Cerca de test", "Convencional", "Test", FECHA_HOY],
            ["PAR-TEST2", "Parada Test 2", "RUT-TEST2", 32.5100, -116.9600,
             "La Mesa", "Blvd. Test", "Frente a test", "SITT", "Test", FECHA_HOY],
        ],
        "UNIDADES": [
            ["UNI-TEST1", "AT-TEST", "RUT-TEST1", "Mercedes Test", "Sí",
             "Test", FECHA_HOY],
            ["UNI-TEST2", "AL-TEST", "RUT-TEST2", "Volvo Test", "No",
             "Test", FECHA_HOY],
        ],
        "PUNTOS_DE_INTERES": [
            ["POI-TEST1", "POI Test 1", "Universidad", 32.5255, -117.0130,
             "Centro", "Av. Test", "Test", FECHA_HOY],
            ["POI-TEST2", "POI Test 2", "Hospital", 32.5185, -117.0060,
             "Zona Río", "Blvd. Test", "Test", FECHA_HOY],
        ],
        "INCIDENCIAS_HISTORICAS": [
            ["INC-TEST1", "2026-02-24", "Retraso", "Incidencia de prueba",
             "RUT-TEST1", "Test", FECHA_HOY],
            ["INC-TEST2", "2026-02-24", "Desvío", "Incidencia de prueba 2",
             "RUT-TEST2", "Test", FECHA_HOY],
        ]
    }

    for nombre_hoja, datos in pruebas.items():
        escritos = manager.escribir_datos(nombre_hoja, datos)
        logger.info(f"✅ Test {nombre_hoja}: {escritos} registros escritos")

    # Resumen
    resumen = manager.obtener_resumen()
    logger.info("\n📊 RESUMEN TEST:")
    for hoja, count in resumen.items():
        logger.info(f"   {hoja}: {count} registros")

    logger.info("\n✅ TEST COMPLETADO EXITOSAMENTE")
    return True


def ejecutar_fase(num_fase, config, manager, scraper):
    """
    Ejecuta una fase específica del scraping.
    Consulta datos existentes para evitar duplicados.
    
    Args:
        num_fase: Número de fase (1-5)
        config: Configuración completa
        manager: GoogleSheetsManager
        scraper: WebScraper
    """
    fases_info = {
        1: "RUTAS",
        2: "PARADAS",
        3: "UNIDADES",
        4: "PUNTOS_DE_INTERES",
        5: "INCIDENCIAS_HISTORICAS",
    }

    if num_fase not in fases_info:
        logger.error(f"❌ Fase {num_fase} no válida (use 1-5)")
        return

    nombre_hoja = fases_info[num_fase]
    logger.info(f"\n{'=' * 60}")
    logger.info(f"🔄 FASE {num_fase}: {nombre_hoja}")
    logger.info(f"{'=' * 60}")

    try:
        # Obtener offset de ID para continuar secuencia
        offset = manager.obtener_max_id_numerico(nombre_hoja)
        logger.info(f"📊 Último ID existente en {nombre_hoja}: {offset}")

        # Generar datos según la fase, pasando offset y datos existentes
        if num_fase == 1:
            nombres = manager.obtener_valores_columna(nombre_hoja, 1)  # Nombre_Ruta
            logger.info(f"📊 Rutas existentes: {len(nombres)}")
            datos = generar_rutas(config, scraper, offset=offset, nombres_existentes=nombres)
        elif num_fase == 2:
            rutas_con_paradas = manager.obtener_valores_columna(nombre_hoja, 2)  # ID_Ruta
            logger.info(f"📊 Rutas que ya tienen paradas: {len(rutas_con_paradas)}")
            datos = generar_paradas(config, offset=offset, rutas_existentes=rutas_con_paradas)
        elif num_fase == 3:
            rutas_con_unidades = manager.obtener_valores_columna(nombre_hoja, 2)  # Ruta_Asignada
            logger.info(f"📊 Rutas que ya tienen unidades: {len(rutas_con_unidades)}")
            datos = generar_unidades(config, offset=offset, rutas_existentes=rutas_con_unidades)
        elif num_fase == 4:
            nombres = manager.obtener_valores_columna(nombre_hoja, 1)  # Nombre
            logger.info(f"📊 POIs existentes: {len(nombres)}")
            datos = generar_puntos_interes(config, offset=offset, nombres_existentes=nombres)
        elif num_fase == 5:
            datos = generar_incidencias(config, scraper, offset=offset)

        if datos:
            escritos = manager.escribir_datos(nombre_hoja, datos)
            logger.info(f"✅ Fase {num_fase} completada: {escritos} registros nuevos")
        else:
            logger.info(f"✔ Fase {num_fase}: No hay datos nuevos que agregar")
    except Exception as e:
        logger.error(f"❌ Error en Fase {num_fase}: {e}")


def ejecucion_completa(config):
    """Ejecuta todas las 5 fases del scraping."""
    inicio = datetime.now()
    logger.info("=" * 60)
    logger.info("🚀 INICIO DE SCRAPING COMPLETO")
    logger.info(f"📅 Fecha: {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # Inicializar conexión a Google Sheets
    gs_config = config["google_sheets"]
    manager = GoogleSheetsManager(
        gs_config["credentials_file"],
        gs_config["spreadsheet_id"]
    )
    manager.verificar_o_crear_hojas()

    # Inicializar scraper web
    scraper = WebScraper(config.get("scraping", {}))

    # Ejecutar las 5 fases en orden
    for fase in range(1, 6):
        try:
            ejecutar_fase(fase, config, manager, scraper)
        except Exception as e:
            logger.error(f"❌ Error crítico en Fase {fase}: {e}")
            logger.info("⏩ Continuando con la siguiente fase...")

    # Resumen final
    fin = datetime.now()
    duracion = fin - inicio
    logger.info("\n" + "=" * 60)
    logger.info("📊 RESUMEN FINAL")
    logger.info("=" * 60)

    resumen = manager.obtener_resumen()
    for hoja, count in resumen.items():
        emoji = "📋" if hoja != "TOTAL" else "🎯"
        logger.info(f"   {emoji} {hoja}: {count} registros")

    logger.info(f"\n⏱ Duración total: {duracion}")
    meta = 6000
    total = resumen.get("TOTAL", 0)
    porcentaje = (total / meta * 100) if meta > 0 else 0
    logger.info(f"🎯 Meta: {meta} registros | Alcanzados: {total} ({porcentaje:.1f}%)")

    if total >= meta:
        logger.info("🎉 ¡META ALCANZADA!")
    else:
        logger.info(f"📈 Faltan {meta - total} registros para la meta")
        logger.info("💡 Sugerencia: Ejecuta de nuevo para agregar más datos")

    logger.info("\n✅ SCRAPING COMPLETADO")
    return resumen


def main():
    """Punto de entrada principal del script."""
    parser = argparse.ArgumentParser(
        description="Scraper de Transporte Público - Tijuana, B.C."
    )
    parser.add_argument(
        "--test", action="store_true",
        help="Ejecutar en modo test (solo verifica conexión)"
    )
    parser.add_argument(
        "--fase", type=int, choices=[1, 2, 3, 4, 5],
        help="Ejecutar solo una fase específica (1-5)"
    )
    args = parser.parse_args()

    logger.info("🚌 Scraper de Transporte Público - Tijuana, B.C.")
    logger.info("=" * 60)

    config = cargar_configuracion()

    if args.test:
        modo_test(config)
    elif args.fase:
        gs_config = config["google_sheets"]
        manager = GoogleSheetsManager(
            gs_config["credentials_file"],
            gs_config["spreadsheet_id"]
        )
        manager.verificar_o_crear_hojas()
        scraper = WebScraper(config.get("scraping", {}))
        ejecutar_fase(args.fase, config, manager, scraper)
    else:
        ejecucion_completa(config)


if __name__ == "__main__":
    main()
