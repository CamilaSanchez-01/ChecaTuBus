"""
Módulo de gestión de Google Sheets.
Maneja la conexión, creación de hojas y escritura de datos.
"""

import gspread
from google.oauth2.service_account import Credentials
import logging
import time

logger = logging.getLogger(__name__)

# Definición de encabezados para cada hoja
ENCABEZADOS = {
    "RUTAS": [
        "ID_Ruta", "Nombre_Ruta", "Concesionario", "Tipo_Servicio",
        "Zonas_Conecta", "Calles_Principales", "Fuente", "Fecha_Extraccion"
    ],
    "PARADAS": [
        "ID_Parada", "Nombre_Parada", "ID_Ruta", "Latitud", "Longitud",
        "Colonia", "Calle", "Referencias_Cercanas", "Tipo_Parada",
        "Fuente", "Fecha_Extraccion"
    ],
    "UNIDADES": [
        "ID_Unidad", "Numero_Economico", "Ruta_Asignada", "Modelo",
        "GPS", "Fuente", "Fecha_Extraccion"
    ],
    "PUNTOS_DE_INTERES": [
        "ID_Punto", "Nombre", "Tipo", "Latitud", "Longitud",
        "Colonia", "Direccion", "Fuente", "Fecha_Extraccion"
    ],
    "INCIDENCIAS_HISTORICAS": [
        "ID_Incidencia", "Fecha", "Tipo_Incidencia", "Descripcion",
        "Ruta_Afectada", "Fuente", "Fecha_Extraccion"
    ]
}


class GoogleSheetsManager:
    """Gestiona la conexión y operaciones con Google Sheets."""

    def __init__(self, credentials_file, spreadsheet_id):
        """
        Inicializa la conexión con Google Sheets.
        
        Args:
            credentials_file: Ruta al archivo credentials.json
            spreadsheet_id: ID de la hoja de cálculo de Google
        """
        self.credentials_file = credentials_file
        self.spreadsheet_id = spreadsheet_id
        self.client = None
        self.spreadsheet = None
        self._conectar()

    def _conectar(self):
        """Establece la conexión con Google Sheets usando cuenta de servicio."""
        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = Credentials.from_service_account_file(
                self.credentials_file, scopes=scopes
            )
            self.client = gspread.authorize(creds)
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            logger.info("✅ Conexión exitosa con Google Sheets")
        except Exception as e:
            logger.error(f"❌ Error al conectar con Google Sheets: {e}")
            raise

    def verificar_o_crear_hojas(self):
        """Verifica que existan todas las hojas necesarias y las crea si faltan."""
        hojas_existentes = [ws.title for ws in self.spreadsheet.worksheets()]
        logger.info(f"Hojas existentes: {hojas_existentes}")

        for nombre_hoja, encabezados in ENCABEZADOS.items():
            if nombre_hoja not in hojas_existentes:
                try:
                    ws = self.spreadsheet.add_worksheet(
                        title=nombre_hoja, rows=1000, cols=len(encabezados)
                    )
                    ws.append_row(encabezados, value_input_option="RAW")
                    logger.info(f"✅ Hoja '{nombre_hoja}' creada con encabezados")
                    time.sleep(1)  # Evitar rate limit de la API
                except Exception as e:
                    logger.error(f"❌ Error al crear hoja '{nombre_hoja}': {e}")
            else:
                # Verificar que tenga encabezados
                ws = self.spreadsheet.worksheet(nombre_hoja)
                primera_fila = ws.row_values(1)
                if not primera_fila:
                    ws.append_row(encabezados, value_input_option="RAW")
                    logger.info(f"✅ Encabezados añadidos a '{nombre_hoja}'")
                else:
                    logger.info(f"✔ Hoja '{nombre_hoja}' ya existe con encabezados")

        # Eliminar la hoja por defecto "Sheet1" si existe y no la necesitamos
        try:
            hoja_default = self.spreadsheet.worksheet("Sheet1")
            if len(self.spreadsheet.worksheets()) > 1:
                self.spreadsheet.del_worksheet(hoja_default)
                logger.info("🗑 Hoja 'Sheet1' eliminada")
        except gspread.exceptions.WorksheetNotFound:
            pass
        except Exception:
            pass

    def escribir_datos(self, nombre_hoja, filas):
        """
        Escribe filas de datos en una hoja (modo append).
        Divide en lotes para respetar límites de la API.
        
        Args:
            nombre_hoja: Nombre de la pestaña en Google Sheets
            filas: Lista de listas con los datos a escribir
        """
        if not filas:
            logger.warning(f"⚠ No hay datos para escribir en '{nombre_hoja}'")
            return 0

        try:
            ws = self.spreadsheet.worksheet(nombre_hoja)
            total = len(filas)
            lote_tamano = 500  # Máximo de filas por petición
            escritos = 0

            for i in range(0, total, lote_tamano):
                lote = filas[i:i + lote_tamano]
                # Convertir todo a string para evitar problemas de tipo
                lote_str = []
                for fila in lote:
                    lote_str.append([str(v) if v is not None else "" for v in fila])

                ws.append_rows(lote_str, value_input_option="RAW")
                escritos += len(lote)
                logger.info(
                    f"📝 '{nombre_hoja}': {escritos}/{total} filas escritas"
                )
                time.sleep(2)  # Pausa entre lotes para evitar rate limit

            logger.info(f"✅ '{nombre_hoja}': {total} filas escritas en total")
            return total
        except Exception as e:
            logger.error(f"❌ Error al escribir en '{nombre_hoja}': {e}")
            return 0

    def contar_registros(self, nombre_hoja):
        """Cuenta los registros existentes en una hoja (excluyendo encabezado)."""
        try:
            ws = self.spreadsheet.worksheet(nombre_hoja)
            return len(ws.get_all_values()) - 1  # -1 por encabezado
        except Exception:
            return 0

    def obtener_valores_columna(self, nombre_hoja, columna_idx):
        """
        Retorna un set con los valores de una columna específica (excluyendo encabezado).

        Args:
            nombre_hoja: Nombre de la pestaña
            columna_idx: Índice de columna (0-based)

        Returns:
            set con los valores únicos de esa columna
        """
        try:
            ws = self.spreadsheet.worksheet(nombre_hoja)
            todas = ws.get_all_values()
            if len(todas) <= 1:
                return set()
            return {fila[columna_idx] for fila in todas[1:] if len(fila) > columna_idx}
        except Exception as e:
            logger.warning(f"⚠ Error al leer columna {columna_idx} de '{nombre_hoja}': {e}")
            return set()

    def obtener_max_id_numerico(self, nombre_hoja):
        """
        Lee la columna ID (columna 0) y retorna el mayor número encontrado.
        Ejemplo: si la hoja tiene IDs RUT-0001 a RUT-0063, retorna 63.

        Returns:
            int: mayor número de ID, o 0 si no hay datos
        """
        ids = self.obtener_valores_columna(nombre_hoja, 0)
        if not ids:
            return 0
        max_num = 0
        for id_val in ids:
            try:
                # Extraer la parte numérica después del último guión
                num = int(id_val.rsplit("-", 1)[-1])
                if num > max_num:
                    max_num = num
            except (ValueError, IndexError):
                continue
        return max_num

    def obtener_resumen(self):
        """Retorna un resumen del conteo de registros por hoja."""
        resumen = {}
        total = 0
        for nombre_hoja in ENCABEZADOS:
            count = self.contar_registros(nombre_hoja)
            resumen[nombre_hoja] = count
            total += count
        resumen["TOTAL"] = total
        return resumen
